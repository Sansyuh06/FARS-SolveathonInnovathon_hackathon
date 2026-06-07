"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import {
  ChevronDown,
  Search,
  HelpCircle,
  Package,
  Shield,
  Wrench,
  CreditCard,
  Truck,
  MessageCircle,
} from "lucide-react";
import { Input } from "@/components/ui/input";

const categories = [
  { id: "general", name: "General", icon: HelpCircle },
  { id: "ordering", name: "Ordering", icon: Package },
  { id: "technical", name: "Technical", icon: Wrench },
  { id: "security", name: "Security", icon: Shield },
  { id: "billing", name: "Billing", icon: CreditCard },
  { id: "shipping", name: "Shipping", icon: Truck },
];

const faqs = [
  {
    category: "general",
    question: "What is FARS?",
    answer: "FARS (Fully Automated Robotic System) provides intelligent humanoid robots designed for healthcare, education, and enterprise environments. Our robots feature AI-powered face recognition, autonomous navigation, voice interaction, and real-time analytics."
  },
  {
    category: "general",
    question: "What environments are FARS robots suitable for?",
    answer: "FARS robots are designed for hospitals, senior care facilities, schools, universities, corporate offices, hotels, and retail environments. They excel in any space requiring automated assistance, visitor management, or interactive engagement."
  },
  {
    category: "general",
    question: "Do FARS robots replace human workers?",
    answer: "No, FARS robots are designed to augment human capabilities, not replace them. They handle repetitive tasks, provide 24/7 coverage for basic interactions, and free up staff to focus on more complex, human-centered activities."
  },
  {
    category: "ordering",
    question: "How do I order a FARS robot?",
    answer: "Visit our Order page to configure your robot. Select your preferred model (Sentinel, Guardian, or Apex), add any optional features, provide delivery details, and submit your order. Our team will contact you within 24 hours to finalize the arrangement."
  },
  {
    category: "ordering",
    question: "What configurations are available?",
    answer: "We offer three configurations: Sentinel (basic) at $15,000 for small facilities, Guardian (advanced) at $35,000 for medium enterprises, and Apex (enterprise) at $75,000 for large institutions with maximum capabilities."
  },
  {
    category: "ordering",
    question: "Can I customize my robot?",
    answer: "Yes, you can add optional features like Elderly Care Mode, Multilingual Pack (20+ languages), HD Camera Array, Premium Audio, 5G Connectivity, and Extended Warranty during the ordering process."
  },
  {
    category: "technical",
    question: "What AI capabilities do the robots have?",
    answer: "FARS robots feature facial recognition (98%+ accuracy), natural language processing, voice interaction, emotion detection, and contextual awareness. The AI continuously learns and improves from interactions."
  },
  {
    category: "technical",
    question: "How does navigation work?",
    answer: "Our robots use LiDAR sensors and computer vision for autonomous navigation with ±2cm accuracy. During setup, the robot maps your space, and you can designate waypoints and restricted areas through the dashboard."
  },
  {
    category: "technical",
    question: "What is the battery life?",
    answer: "Battery life varies by configuration: Sentinel offers 8 hours, Guardian provides 12 hours, and Apex delivers 24 hours of continuous operation. All models feature automatic return-to-charging and can be configured for optimal battery management."
  },
  {
    category: "technical",
    question: "Is there an API for integration?",
    answer: "Yes, we provide comprehensive REST and WebSocket APIs. SDKs are available for Python, JavaScript, Java, and C#. Visit our Documentation page for complete API reference and code examples."
  },
  {
    category: "security",
    question: "How is data protected?",
    answer: "All data is encrypted with TLS 1.3 in transit and AES-256 at rest. Face data is encrypted on-device. We are SOC 2 Type II certified and comply with HIPAA, FERPA, and GDPR requirements."
  },
  {
    category: "security",
    question: "Who has access to robot data?",
    answer: "You have full control over data access through role-based permissions. Only authorized personnel can access specific features and data. All access is logged for audit purposes."
  },
  {
    category: "security",
    question: "Can the robot be hacked?",
    answer: "We implement multiple security layers including encrypted communications, secure boot, regular security updates, and penetration testing. Our dedicated security team monitors for threats 24/7."
  },
  {
    category: "billing",
    question: "What payment methods do you accept?",
    answer: "We accept wire transfers, corporate purchase orders, and major credit cards for enterprise customers. Payment terms and financing options are available for qualified institutions."
  },
  {
    category: "billing",
    question: "Is there a subscription fee?",
    answer: "The robot purchase is one-time. Optional cloud services (advanced analytics, priority support, software updates) are available as monthly subscriptions starting at $299/month."
  },
  {
    category: "shipping",
    question: "Where do you ship?",
    answer: "We currently ship to India, Singapore, and the United States. Expansion to additional countries in Southeast Asia and Europe is planned for 2025. Contact us for availability in your region."
  },
  {
    category: "shipping",
    question: "How long does delivery take?",
    answer: "Standard delivery takes 4-6 weeks from order confirmation. This includes manufacturing, quality testing, and shipping. Expedited delivery (2-3 weeks) is available for an additional fee."
  },
  {
    category: "shipping",
    question: "Is installation included?",
    answer: "Yes, professional installation and initial setup are included with all orders. Our technicians will map your space, configure waypoints, train your staff, and ensure optimal operation."
  },
];

export default function FAQPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [openItems, setOpenItems] = useState<string[]>([]);

  const filteredFaqs = faqs.filter(faq => {
    const matchesSearch = searchQuery === "" || 
      faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      faq.answer.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = !activeCategory || faq.category === activeCategory;
    return matchesSearch && matchesCategory;
  });

  const toggleItem = (question: string) => {
    setOpenItems(prev => 
      prev.includes(question) ? prev.filter(q => q !== question) : [...prev, question]
    );
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <div className="pt-28 pb-16 px-4">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-12"
          >
            <h1 className="text-4xl sm:text-5xl font-bold mb-4" style={{ fontFamily: "'Syne', sans-serif" }}>
              Frequently Asked <span className="gradient-text">Questions</span>
            </h1>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Find answers to common questions about FARS robots, ordering, and support.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mb-8"
          >
            <div className="relative max-w-md mx-auto">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <Input
                placeholder="Search questions..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="flex flex-wrap justify-center gap-2 mb-12"
          >
            <Button
              variant={activeCategory === null ? "default" : "outline"}
              size="sm"
              onClick={() => setActiveCategory(null)}
              className="rounded-full"
            >
              All
            </Button>
            {categories.map((cat) => (
              <Button
                key={cat.id}
                variant={activeCategory === cat.id ? "default" : "outline"}
                size="sm"
                onClick={() => setActiveCategory(cat.id)}
                className="rounded-full"
              >
                <cat.icon className="w-4 h-4 mr-1" />
                {cat.name}
              </Button>
            ))}
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="space-y-3"
          >
            {filteredFaqs.map((faq, i) => (
              <motion.div
                key={faq.question}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.05 * i }}
                className="rounded-xl border border-border overflow-hidden"
              >
                <button
                  onClick={() => toggleItem(faq.question)}
                  className="w-full flex items-center justify-between p-4 text-left hover:bg-card transition-colors"
                >
                  <span className="font-medium pr-4">{faq.question}</span>
                  <ChevronDown className={`w-5 h-5 shrink-0 text-muted-foreground transition-transform ${
                    openItems.includes(faq.question) ? "rotate-180" : ""
                  }`} />
                </button>
                {openItems.includes(faq.question) && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="px-4 pb-4"
                  >
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {faq.answer}
                    </p>
                  </motion.div>
                )}
              </motion.div>
            ))}
          </motion.div>

          {filteredFaqs.length === 0 && (
            <div className="text-center py-12">
              <HelpCircle className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No questions match your search.</p>
            </div>
          )}

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mt-16 p-8 rounded-2xl bg-card border border-border text-center"
          >
            <MessageCircle className="w-12 h-12 mx-auto text-primary mb-4" />
            <h2 className="text-xl font-bold mb-2" style={{ fontFamily: "'Syne', sans-serif" }}>
              Still have questions?
            </h2>
            <p className="text-muted-foreground mb-6">
              Our support team is here to help you with any questions not covered above.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button asChild className="rounded-full">
                <Link href="/contact">Contact Support</Link>
              </Button>
              <Button asChild variant="outline" className="rounded-full">
                <Link href="/docs">View Documentation</Link>
              </Button>
            </div>
          </motion.div>
        </div>
      </div>

      <Footer />
    </div>
  );
}
