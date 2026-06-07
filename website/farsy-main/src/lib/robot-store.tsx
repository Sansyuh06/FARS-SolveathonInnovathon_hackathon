"use client";

import { createContext, useContext, useState, ReactNode, useCallback } from "react";

export interface Robot {
  id: string;
  serialNumber: string;
  name: string;
  model: "basic" | "advanced" | "enterprise";
  status: "online" | "offline" | "maintenance";
  battery: number;
  location: string;
  assignedTo?: string;
  institutionId?: string;
  features: string[];
  lastActive: string;
  totalHours: number;
}

export interface Order {
  id: string;
  institutionName: string;
  address: string;
  contactPerson: string;
  contactEmail: string;
  contactPhone: string;
  model: "basic" | "advanced" | "enterprise";
  features: string[];
  quantity: number;
  totalPrice: number;
  status: "pending" | "approved" | "shipped" | "delivered" | "cancelled";
  createdAt: string;
  userId: string;
}

export interface RobotLog {
  id: string;
  robotId: string;
  type: "command" | "status" | "error" | "attendance";
  message: string;
  timestamp: string;
  details?: Record<string, unknown>;
}

export interface AttendanceLog {
  id: string;
  robotId: string;
  personName: string;
  personId: string;
  action: "check-in" | "check-out";
  timestamp: string;
  confidence: number;
}

export interface SupportTicket {
  id: string;
  userId: string;
  robotId?: string;
  subject: string;
  description: string;
  status: "open" | "in-progress" | "resolved" | "closed";
  priority: "low" | "medium" | "high" | "critical";
  createdAt: string;
  updatedAt: string;
}

export interface SensorData {
  distance: number;
  battery: number;
  temperature: number;
  humidity: number;
  cpuUsage: number;
  memoryUsage: number;
}

interface RobotStoreContextType {
  robots: Robot[];
  orders: Order[];
  logs: RobotLog[];
  attendanceLogs: AttendanceLog[];
  tickets: SupportTicket[];
  sensorData: Record<string, SensorData>;
  addOrder: (order: Omit<Order, "id" | "createdAt" | "status">) => Order;
  updateOrderStatus: (orderId: string, status: Order["status"]) => void;
  sendCommand: (robotId: string, command: string) => void;
  addTicket: (ticket: Omit<SupportTicket, "id" | "createdAt" | "updatedAt" | "status">) => void;
  updateTicketStatus: (ticketId: string, status: SupportTicket["status"]) => void;
  assignRobot: (robotId: string, institutionId: string) => void;
  toggleRobotStatus: (robotId: string) => void;
}

const INITIAL_ROBOTS: Robot[] = [
  {
    id: "R001",
    serialNumber: "FARS-2024-001",
    name: "Atlas-01",
    model: "enterprise",
    status: "online",
    battery: 87,
    location: "Reception Hall A",
    assignedTo: "Metro General Hospital",
    institutionId: "2",
    features: ["Face Recognition", "Navigation", "Elderly Assistance", "Voice Interaction"],
    lastActive: new Date().toISOString(),
    totalHours: 1247,
  },
  {
    id: "R002",
    serialNumber: "FARS-2024-002",
    name: "Nova-02",
    model: "advanced",
    status: "online",
    battery: 65,
    location: "Ward B - Floor 3",
    assignedTo: "Metro General Hospital",
    institutionId: "2",
    features: ["Face Recognition", "Navigation"],
    lastActive: new Date().toISOString(),
    totalHours: 892,
  },
  {
    id: "R003",
    serialNumber: "FARS-2024-003",
    name: "Echo-03",
    model: "basic",
    status: "offline",
    battery: 12,
    location: "Charging Station",
    assignedTo: "Sunrise Senior Living",
    institutionId: "3",
    features: ["Navigation"],
    lastActive: new Date(Date.now() - 3600000).toISOString(),
    totalHours: 456,
  },
  {
    id: "R004",
    serialNumber: "FARS-2024-004",
    name: "Titan-04",
    model: "enterprise",
    status: "maintenance",
    battery: 45,
    location: "Service Bay",
    features: ["Face Recognition", "Navigation", "Elderly Assistance", "Voice Interaction"],
    lastActive: new Date(Date.now() - 86400000).toISOString(),
    totalHours: 2103,
  },
];

const INITIAL_ORDERS: Order[] = [
  {
    id: "ORD-001",
    institutionName: "City Medical Center",
    address: "456 Healthcare Blvd, Suite 100",
    contactPerson: "Dr. Michael Torres",
    contactEmail: "mtorres@citymed.org",
    contactPhone: "+1 555-0199",
    model: "enterprise",
    features: ["Face Recognition", "Navigation", "Elderly Assistance"],
    quantity: 3,
    totalPrice: 149997,
    status: "pending",
    createdAt: new Date(Date.now() - 172800000).toISOString(),
    userId: "4",
  },
  {
    id: "ORD-002",
    institutionName: "Green Valley School",
    address: "789 Education Lane",
    contactPerson: "Principal Jane Doe",
    contactEmail: "jdoe@gvschool.edu",
    contactPhone: "+1 555-0142",
    model: "advanced",
    features: ["Navigation", "Voice Interaction"],
    quantity: 2,
    totalPrice: 59998,
    status: "approved",
    createdAt: new Date(Date.now() - 604800000).toISOString(),
    userId: "5",
  },
];

const INITIAL_LOGS: RobotLog[] = [
  { id: "L001", robotId: "R001", type: "status", message: "System boot completed successfully", timestamp: new Date().toISOString() },
  { id: "L002", robotId: "R001", type: "command", message: "Navigation initiated to Reception Hall A", timestamp: new Date(Date.now() - 300000).toISOString() },
  { id: "L003", robotId: "R002", type: "attendance", message: "Face recognition: Dr. Sarah Chen identified", timestamp: new Date(Date.now() - 600000).toISOString() },
  { id: "L004", robotId: "R003", type: "error", message: "Low battery warning - initiating return to charging station", timestamp: new Date(Date.now() - 900000).toISOString() },
];

const INITIAL_ATTENDANCE: AttendanceLog[] = [
  { id: "A001", robotId: "R001", personName: "Dr. Sarah Chen", personId: "EMP001", action: "check-in", timestamp: new Date(Date.now() - 28800000).toISOString(), confidence: 98.5 },
  { id: "A002", robotId: "R001", personName: "Nurse James Wilson", personId: "EMP002", action: "check-in", timestamp: new Date(Date.now() - 27000000).toISOString(), confidence: 97.2 },
  { id: "A003", robotId: "R002", personName: "Dr. Michael Torres", personId: "EMP003", action: "check-in", timestamp: new Date(Date.now() - 25200000).toISOString(), confidence: 99.1 },
  { id: "A004", robotId: "R001", personName: "Dr. Sarah Chen", personId: "EMP001", action: "check-out", timestamp: new Date(Date.now() - 3600000).toISOString(), confidence: 98.8 },
];

const INITIAL_TICKETS: SupportTicket[] = [
  {
    id: "TKT-001",
    userId: "2",
    robotId: "R001",
    subject: "Navigation calibration needed",
    description: "Atlas-01 seems to have slight drift when navigating to Ward C. Requesting recalibration.",
    status: "in-progress",
    priority: "medium",
    createdAt: new Date(Date.now() - 86400000).toISOString(),
    updatedAt: new Date(Date.now() - 43200000).toISOString(),
  },
];

const RobotStoreContext = createContext<RobotStoreContextType | undefined>(undefined);

export function RobotStoreProvider({ children }: { children: ReactNode }) {
  const [robots, setRobots] = useState<Robot[]>(INITIAL_ROBOTS);
  const [orders, setOrders] = useState<Order[]>(INITIAL_ORDERS);
  const [logs, setLogs] = useState<RobotLog[]>(INITIAL_LOGS);
  const [attendanceLogs] = useState<AttendanceLog[]>(INITIAL_ATTENDANCE);
  const [tickets, setTickets] = useState<SupportTicket[]>(INITIAL_TICKETS);
  const [sensorData] = useState<Record<string, SensorData>>({
    R001: { distance: 2.4, battery: 87, temperature: 38.2, humidity: 45, cpuUsage: 34, memoryUsage: 52 },
    R002: { distance: 1.8, battery: 65, temperature: 37.8, humidity: 48, cpuUsage: 42, memoryUsage: 61 },
    R003: { distance: 0.5, battery: 12, temperature: 35.1, humidity: 42, cpuUsage: 8, memoryUsage: 23 },
    R004: { distance: 0, battery: 45, temperature: 36.5, humidity: 44, cpuUsage: 0, memoryUsage: 15 },
  });

  const addOrder = useCallback((orderData: Omit<Order, "id" | "createdAt" | "status">) => {
    const newOrder: Order = {
      ...orderData,
      id: `ORD-${Date.now()}`,
      createdAt: new Date().toISOString(),
      status: "pending",
    };
    setOrders((prev) => [newOrder, ...prev]);
    return newOrder;
  }, []);

  const updateOrderStatus = useCallback((orderId: string, status: Order["status"]) => {
    setOrders((prev) => prev.map((o) => (o.id === orderId ? { ...o, status } : o)));
  }, []);

  const sendCommand = useCallback((robotId: string, command: string) => {
    const newLog: RobotLog = {
      id: `L${Date.now()}`,
      robotId,
      type: "command",
      message: `Command executed: ${command}`,
      timestamp: new Date().toISOString(),
    };
    setLogs((prev) => [newLog, ...prev]);

    if (command === "start") {
      setRobots((prev) => prev.map((r) => (r.id === robotId ? { ...r, status: "online" } : r)));
    } else if (command === "stop") {
      setRobots((prev) => prev.map((r) => (r.id === robotId ? { ...r, status: "offline" } : r)));
    }
  }, []);

  const addTicket = useCallback((ticketData: Omit<SupportTicket, "id" | "createdAt" | "updatedAt" | "status">) => {
    const newTicket: SupportTicket = {
      ...ticketData,
      id: `TKT-${Date.now()}`,
      status: "open",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    setTickets((prev) => [newTicket, ...prev]);
  }, []);

  const updateTicketStatus = useCallback((ticketId: string, status: SupportTicket["status"]) => {
    setTickets((prev) =>
      prev.map((t) => (t.id === ticketId ? { ...t, status, updatedAt: new Date().toISOString() } : t))
    );
  }, []);

  const assignRobot = useCallback((robotId: string, institutionId: string) => {
    setRobots((prev) => prev.map((r) => (r.id === robotId ? { ...r, institutionId } : r)));
  }, []);

  const toggleRobotStatus = useCallback((robotId: string) => {
    setRobots((prev) =>
      prev.map((r) => {
        if (r.id !== robotId) return r;
        const newStatus = r.status === "online" ? "offline" : "online";
        return { ...r, status: newStatus };
      })
    );
  }, []);

  return (
    <RobotStoreContext.Provider
      value={{
        robots,
        orders,
        logs,
        attendanceLogs,
        tickets,
        sensorData,
        addOrder,
        updateOrderStatus,
        sendCommand,
        addTicket,
        updateTicketStatus,
        assignRobot,
        toggleRobotStatus,
      }}
    >
      {children}
    </RobotStoreContext.Provider>
  );
}

export function useRobotStore() {
  const context = useContext(RobotStoreContext);
  if (!context) throw new Error("useRobotStore must be used within RobotStoreProvider");
  return context;
}
