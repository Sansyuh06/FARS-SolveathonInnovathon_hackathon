import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type UserRole = 'admin' | 'customer' | 'operator';

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  institution?: string;
  phone?: string;
  createdAt: string;
}

export interface Robot {
  id: string;
  name: string;
  serialNumber: string;
  configuration: 'basic' | 'advanced' | 'enterprise';
  status: 'online' | 'offline' | 'maintenance';
  batteryLevel: number;
  lastSeen: string;
  institutionId: string;
  features: string[];
  location?: string;
}

export interface Order {
  id: string;
  userId: string;
  robotConfiguration: 'basic' | 'advanced' | 'enterprise';
  features: string[];
  totalPrice: number;
  status: 'pending' | 'confirmed' | 'processing' | 'shipped' | 'delivered';
  institutionName: string;
  address: string;
  contactPerson: string;
  phone: string;
  createdAt: string;
}

export interface AttendanceLog {
  id: string;
  robotId: string;
  personName: string;
  personId: string;
  timestamp: string;
  confidence: number;
  imageUrl?: string;
}

export interface RobotLog {
  id: string;
  robotId: string;
  type: 'navigation' | 'interaction' | 'error' | 'system';
  message: string;
  timestamp: string;
}

export interface Command {
  id: string;
  robotId: string;
  command: string;
  status: 'pending' | 'executed' | 'failed';
  timestamp: string;
  response?: string;
}

export interface SupportTicket {
  id: string;
  userId: string;
  robotId?: string;
  subject: string;
  description: string;
  status: 'open' | 'in_progress' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  createdAt: string;
  updatedAt: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  signup: (data: { email: string; password: string; name: string; role?: UserRole; institution?: string; phone?: string }) => Promise<boolean>;
  logout: () => void;
}

interface DataState {
  robots: Robot[];
  orders: Order[];
  attendanceLogs: AttendanceLog[];
  robotLogs: RobotLog[];
  commands: Command[];
  supportTickets: SupportTicket[];
  users: User[];
  
  // Actions
  addRobot: (robot: Robot) => void;
  updateRobot: (id: string, updates: Partial<Robot>) => void;
  addOrder: (order: Order) => void;
  updateOrder: (id: string, updates: Partial<Order>) => void;
  addAttendanceLog: (log: AttendanceLog) => void;
  addRobotLog: (log: RobotLog) => void;
  addCommand: (command: Command) => void;
  updateCommand: (id: string, updates: Partial<Command>) => void;
  addSupportTicket: (ticket: SupportTicket) => void;
  updateSupportTicket: (id: string, updates: Partial<SupportTicket>) => void;
}

// Mock users for demo
const mockUsers: User[] = [
  { id: '1', email: 'admin@fars.in', name: 'Admin User', role: 'admin', createdAt: '2024-01-01' },
  { id: '2', email: 'demo@school.edu', name: 'School Admin', role: 'customer', institution: 'Demo School', createdAt: '2024-02-01' },
  { id: '3', email: 'operator@fars.in', name: 'Robot Operator', role: 'operator', createdAt: '2024-03-01' },
];

// Mock data for demo
const mockRobots: Robot[] = [
  {
    id: 'r1',
    name: 'FARS-EDU-001',
    serialNumber: 'FARS2024001',
    configuration: 'advanced',
    status: 'online',
    batteryLevel: 87,
    lastSeen: new Date().toISOString(),
    institutionId: '2',
    features: ['face_recognition', 'navigation', 'voice'],
    location: 'Main Building - Reception',
  },
  {
    id: 'r2',
    name: 'FARS-EDU-002',
    serialNumber: 'FARS2024002',
    configuration: 'basic',
    status: 'offline',
    batteryLevel: 23,
    lastSeen: new Date(Date.now() - 3600000).toISOString(),
    institutionId: '2',
    features: ['face_recognition', 'navigation'],
    location: 'Library',
  },
];

const mockAttendanceLogs: AttendanceLog[] = [
  { id: 'a1', robotId: 'r1', personName: 'John Doe', personId: 'STU001', timestamp: new Date().toISOString(), confidence: 98.5 },
  { id: 'a2', robotId: 'r1', personName: 'Jane Smith', personId: 'STU002', timestamp: new Date(Date.now() - 300000).toISOString(), confidence: 97.2 },
  { id: 'a3', robotId: 'r1', personName: 'Mike Johnson', personId: 'STU003', timestamp: new Date(Date.now() - 600000).toISOString(), confidence: 99.1 },
];

const mockRobotLogs: RobotLog[] = [
  { id: 'l1', robotId: 'r1', type: 'system', message: 'System startup complete', timestamp: new Date().toISOString() },
  { id: 'l2', robotId: 'r1', type: 'navigation', message: 'Navigating to Reception', timestamp: new Date(Date.now() - 60000).toISOString() },
  { id: 'l3', robotId: 'r1', type: 'interaction', message: 'User interaction: Provided directions to Lab 3', timestamp: new Date(Date.now() - 120000).toISOString() },
];

const mockOrders: Order[] = [
  {
    id: 'o1',
    userId: '2',
    robotConfiguration: 'advanced',
    features: ['face_recognition', 'navigation', 'voice', 'elderly_assistance'],
    totalPrice: 35000,
    status: 'delivered',
    institutionName: 'Demo School',
    address: '123 Education Lane, Bangalore',
    contactPerson: 'School Admin',
    phone: '+91 98765 43210',
    createdAt: '2024-01-15',
  },
];

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      login: async (email: string, password: string) => {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 500));
        const user = mockUsers.find(u => u.email === email);
        if (user && password === 'demo123') {
          set({ user, isAuthenticated: true });
          return true;
        }
        return false;
      },
      signup: async (data) => {
        await new Promise(resolve => setTimeout(resolve, 500));
        const newUser: User = {
          id: `user-${Date.now()}`,
          email: data.email,
          name: data.name,
          role: data.role || 'customer',
          institution: data.institution,
          phone: data.phone,
          createdAt: new Date().toISOString(),
        };
        mockUsers.push(newUser);
        set({ user: newUser, isAuthenticated: true });
        return true;
      },
      logout: () => set({ user: null, isAuthenticated: false }),
    }),
    {
      name: 'fars-auth',
    }
  )
);

export const useDataStore = create<DataState>()(
  persist(
    (set) => ({
      robots: mockRobots,
      orders: mockOrders,
      attendanceLogs: mockAttendanceLogs,
      robotLogs: mockRobotLogs,
      commands: [],
      supportTickets: [],
      users: mockUsers,

      addRobot: (robot) => set((state) => ({ robots: [...state.robots, robot] })),
      updateRobot: (id, updates) => set((state) => ({
        robots: state.robots.map(r => r.id === id ? { ...r, ...updates } : r)
      })),
      addOrder: (order) => set((state) => ({ orders: [...state.orders, order] })),
      updateOrder: (id, updates) => set((state) => ({
        orders: state.orders.map(o => o.id === id ? { ...o, ...updates } : o)
      })),
      addAttendanceLog: (log) => set((state) => ({ attendanceLogs: [log, ...state.attendanceLogs] })),
      addRobotLog: (log) => set((state) => ({ robotLogs: [log, ...state.robotLogs] })),
      addCommand: (command) => set((state) => ({ commands: [command, ...state.commands] })),
      updateCommand: (id, updates) => set((state) => ({
        commands: state.commands.map(c => c.id === id ? { ...c, ...updates } : c)
      })),
      addSupportTicket: (ticket) => set((state) => ({ supportTickets: [ticket, ...state.supportTickets] })),
      updateSupportTicket: (id, updates) => set((state) => ({
        supportTickets: state.supportTickets.map(t => t.id === id ? { ...t, ...updates } : t)
      })),
    }),
    {
      name: 'fars-data',
    }
  )
);
