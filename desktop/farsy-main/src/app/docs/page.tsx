"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import Link from "next/link";
import {
  Book,
  Code,
  Terminal,
  Cpu,
  Wifi,
  Shield,
  Zap,
  Search,
  ChevronRight,
  ExternalLink,
  Copy,
  Check,
  Bot,
  Settings,
  Play,
  Database,
  Globe,
  Lock,
} from "lucide-react";

const sections = [
  {
    id: "getting-started",
    title: "Getting Started",
    icon: Play,
    items: [
      { id: "introduction", title: "Introduction", content: `FARS (Fully Automated Robotic System) provides intelligent humanoid robots for healthcare, education, and enterprise environments. This documentation covers setup, configuration, and API integration.` },
      { id: "quick-start", title: "Quick Start Guide", content: `1. Power on your FARS robot using the main switch located on the back panel.\n2. Connect to the robot's WiFi network (FARS-XXXX).\n3. Access the setup wizard at http://192.168.4.1\n4. Follow the on-screen instructions to configure your network and initial settings.` },
      { id: "requirements", title: "System Requirements", content: `- WiFi: 802.11ac or newer\n- Network: Stable internet connection (10+ Mbps)\n- Power: 110-240V AC outlet\n- Space: 2m x 2m minimum operating area\n- Ceiling height: 2.5m minimum` },
    ],
  },
  {
    id: "api-reference",
    title: "API Reference",
    icon: Code,
    items: [
      { id: "authentication", title: "Authentication", content: `All API requests require authentication using an API key. Include your key in the Authorization header:\n\nAuthorization: Bearer YOUR_API_KEY\n\nObtain your API key from the FARS Dashboard > Settings > API Keys.` },
      { id: "endpoints", title: "REST Endpoints", content: `Base URL: https://api.fars.in/v1\n\nGET /robots - List all robots\nGET /robots/{id} - Get robot details\nPOST /robots/{id}/command - Send command\nGET /robots/{id}/status - Get current status\nGET /attendance - Get attendance logs\nPOST /navigation/goto - Navigate to location` },
      { id: "websocket", title: "WebSocket API", content: `Connect to real-time updates:\n\nws://api.fars.in/v1/realtime?token=YOUR_TOKEN\n\nEvents:\n- robot.status - Status changes\n- robot.location - Position updates\n- attendance.new - New attendance records\n- alert.triggered - System alerts` },
      { id: "errors", title: "Error Handling", content: `Standard HTTP status codes are used:\n\n200 - Success\n400 - Bad Request\n401 - Unauthorized\n403 - Forbidden\n404 - Not Found\n429 - Rate Limited\n500 - Server Error\n\nAll errors return JSON with "error" and "message" fields.` },
    ],
  },
  {
    id: "robot-control",
    title: "Robot Control",
    icon: Bot,
    items: [
      { id: "commands", title: "Command Reference", content: `Available commands:\n\nNAVIGATE - Move to specified coordinates\nSPEAK - Output voice message\nSCAN - Perform face recognition scan\nRETURN - Return to charging station\nPATROL - Start patrol route\nSTOP - Halt all movement\nREBOOT - Restart robot systems` },
      { id: "navigation", title: "Navigation System", content: `The FARS robot uses LiDAR and computer vision for navigation.\n\nMap Setup:\n1. Enable mapping mode\n2. Manually guide robot through space\n3. Mark key locations (waypoints)\n4. Save and activate map\n\nNavigation accuracy: ±2cm` },
      { id: "voice", title: "Voice Interaction", content: `Voice capabilities include:\n\n- Wake word detection ("Hey FARS")\n- Natural language processing\n- Multi-language support\n- Custom voice responses\n- Volume control (0-100%)\n\nConfigure voice settings in Dashboard > Robot > Voice.` },
    ],
  },
  {
    id: "integration",
    title: "Integration",
    icon: Database,
    items: [
      { id: "webhooks", title: "Webhooks", content: `Set up webhooks to receive real-time notifications:\n\n1. Go to Dashboard > Settings > Webhooks\n2. Add your endpoint URL\n3. Select events to subscribe\n4. Verify with test payload\n\nWebhooks include HMAC signature for verification.` },
      { id: "sdk", title: "SDK Libraries", content: `Official SDKs available:\n\n- Python: pip install fars-sdk\n- JavaScript: npm install @fars/sdk\n- Java: Maven Central (com.fars:sdk)\n- C#: NuGet (FARS.SDK)\n\nAll SDKs provide typed interfaces and async support.` },
      { id: "third-party", title: "Third-Party Integrations", content: `Pre-built integrations:\n\n- Slack - Notifications & commands\n- Microsoft Teams - Status updates\n- Salesforce - CRM sync\n- Google Calendar - Scheduling\n- Zapier - 1000+ app connections` },
    ],
  },
  {
    id: "security",
    title: "Security",
    icon: Shield,
    items: [
      { id: "encryption", title: "Data Encryption", content: `All data is encrypted:\n\n- In transit: TLS 1.3\n- At rest: AES-256\n- Face data: On-device encryption\n- API keys: Hashed with bcrypt\n\nSOC 2 Type II certified.` },
      { id: "access-control", title: "Access Control", content: `Role-based access control (RBAC):\n\n- Admin: Full system access\n- Manager: Robot control + reports\n- Operator: Basic robot control\n- Viewer: Read-only access\n\nConfigure roles in Dashboard > Team > Roles.` },
      { id: "compliance", title: "Compliance", content: `FARS complies with:\n\n- HIPAA (healthcare)\n- FERPA (education)\n- GDPR (data privacy)\n- ISO 27001 (security)\n- SOC 2 Type II (controls)\n\nCompliance reports available on request.` },
    ],
  },
];

const codeExamples = {
  python: `import fars

client = fars.Client(api_key="YOUR_API_KEY")

# Get robot status
robot = client.robots.get("robot_123")
print(f"Battery: {robot.battery_level}%")

# Send navigation command
client.robots.navigate(
    robot_id="robot_123",
    destination="reception",
    speed="normal"
)

# Subscribe to events
@client.on("attendance.new")
def handle_attendance(event):
    print(f"New: {event.person_name}")`,
  javascript: `import { FARSClient } from '@fars/sdk';

const client = new FARSClient({
  apiKey: 'YOUR_API_KEY'
});

// Get robot status
const robot = await client.robots.get('robot_123');
console.log(\`Battery: \${robot.batteryLevel}%\`);

// Send navigation command
await client.robots.navigate({
  robotId: 'robot_123',
  destination: 'reception',
  speed: 'normal'
});

// Subscribe to events
client.on('attendance.new', (event) => {
  console.log(\`New: \${event.personName}\`);
});`,
  curl: `# Get robot status
curl -X GET "https://api.fars.in/v1/robots/robot_123" \\
  -H "Authorization: Bearer YOUR_API_KEY"

# Send navigation command
curl -X POST "https://api.fars.in/v1/robots/robot_123/navigate" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"destination": "reception", "speed": "normal"}'

# Get attendance logs
curl -X GET "https://api.fars.in/v1/attendance?limit=10" \\
  -H "Authorization: Bearer YOUR_API_KEY"`,
};

export default function DocsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [activeSection, setActiveSection] = useState("getting-started");
  const [activeItem, setActiveItem] = useState("introduction");
  const [codeLanguage, setCodeLanguage] = useState<"python" | "javascript" | "curl">("python");
  const [copied, setCopied] = useState(false);

  const currentSection = sections.find((s) => s.id === activeSection);
  const currentItem = currentSection?.items.find((i) => i.id === activeItem);

  const copyCode = () => {
    navigator.clipboard.writeText(codeExamples[codeLanguage]);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const filteredSections = searchQuery
    ? sections.map((section) => ({
        ...section,
        items: section.items.filter(
          (item) =>
            item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            item.content.toLowerCase().includes(searchQuery.toLowerCase())
        ),
      })).filter((section) => section.items.length > 0)
    : sections;

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <div className="pt-24 pb-16">
        <div className="max-w-7xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-12"
          >
            <h1 className="text-4xl sm:text-5xl font-bold mb-4" style={{ fontFamily: "'Syne', sans-serif" }}>
              <span className="gradient-text">Documentation</span>
            </h1>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Everything you need to integrate and control your FARS robots.
            </p>
          </motion.div>

          <div className="flex flex-col lg:flex-row gap-8">
            <aside className="lg:w-72 shrink-0">
              <div className="sticky top-28 space-y-4">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                  <Input
                    placeholder="Search docs..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>

                <nav className="space-y-2">
                  {filteredSections.map((section) => (
                    <div key={section.id}>
                      <button
                        onClick={() => {
                          setActiveSection(section.id);
                          setActiveItem(section.items[0]?.id || "");
                        }}
                        className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                          activeSection === section.id
                            ? "bg-primary/10 text-primary"
                            : "hover:bg-muted"
                        }`}
                      >
                        <section.icon className="w-4 h-4" />
                        {section.title}
                      </button>
                      {activeSection === section.id && (
                        <div className="ml-6 mt-1 space-y-1">
                          {section.items.map((item) => (
                            <button
                              key={item.id}
                              onClick={() => setActiveItem(item.id)}
                              className={`w-full text-left px-3 py-1.5 rounded text-sm transition-colors ${
                                activeItem === item.id
                                  ? "text-primary font-medium"
                                  : "text-muted-foreground hover:text-foreground"
                              }`}
                            >
                              {item.title}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </nav>
              </div>
            </aside>

            <main className="flex-1 min-w-0">
              <motion.div
                key={`${activeSection}-${activeItem}`}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-8"
              >
                {currentItem && (
                  <div className="p-6 rounded-2xl bg-card border border-border">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
                      {currentSection && <currentSection.icon className="w-4 h-4" />}
                      <span>{currentSection?.title}</span>
                      <ChevronRight className="w-4 h-4" />
                      <span className="text-foreground">{currentItem.title}</span>
                    </div>
                    <h2 className="text-2xl font-bold mb-6" style={{ fontFamily: "'Syne', sans-serif" }}>
                      {currentItem.title}
                    </h2>
                    <div className="prose prose-invert max-w-none">
                      <pre className="whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground font-sans">
                        {currentItem.content}
                      </pre>
                    </div>
                  </div>
                )}

                {activeSection === "api-reference" && (
                  <div className="p-6 rounded-2xl bg-card border border-border">
                    <h3 className="text-xl font-bold mb-4" style={{ fontFamily: "'Syne', sans-serif" }}>
                      Code Examples
                    </h3>
                    <div className="flex gap-2 mb-4">
                      {(["python", "javascript", "curl"] as const).map((lang) => (
                        <Button
                          key={lang}
                          variant={codeLanguage === lang ? "default" : "outline"}
                          size="sm"
                          onClick={() => setCodeLanguage(lang)}
                          className="rounded-full capitalize"
                        >
                          {lang}
                        </Button>
                      ))}
                    </div>
                    <div className="relative">
                      <pre className="p-4 rounded-xl bg-background border border-border overflow-x-auto text-sm">
                        <code>{codeExamples[codeLanguage]}</code>
                      </pre>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="absolute top-2 right-2"
                        onClick={copyCode}
                      >
                        {copied ? (
                          <Check className="w-4 h-4 text-primary" />
                        ) : (
                          <Copy className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                )}

                <div className="grid sm:grid-cols-2 gap-4">
                  <div className="p-6 rounded-2xl bg-card border border-border">
                    <Globe className="w-8 h-8 text-primary mb-4" />
                    <h3 className="font-bold mb-2" style={{ fontFamily: "'Syne', sans-serif" }}>
                      API Status
                    </h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      Check real-time API availability and performance metrics.
                    </p>
                    <Button variant="outline" size="sm" className="rounded-full" asChild>
                      <a href="https://status.fars.in" target="_blank" rel="noopener noreferrer">
                        View Status
                        <ExternalLink className="w-4 h-4 ml-2" />
                      </a>
                    </Button>
                  </div>
                  <div className="p-6 rounded-2xl bg-card border border-border">
                    <Terminal className="w-8 h-8 text-primary mb-4" />
                    <h3 className="font-bold mb-2" style={{ fontFamily: "'Syne', sans-serif" }}>
                      API Playground
                    </h3>
                    <p className="text-sm text-muted-foreground mb-4">
                      Test API endpoints directly in your browser.
                    </p>
                    <Button variant="outline" size="sm" className="rounded-full" asChild>
                      <Link href="/login">
                        Open Playground
                        <ExternalLink className="w-4 h-4 ml-2" />
                      </Link>
                    </Button>
                  </div>
                </div>
              </motion.div>
            </main>
          </div>
        </div>
      </div>

      <Footer />
    </div>
  );
}
