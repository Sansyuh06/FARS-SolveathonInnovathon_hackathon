"use client";

import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { motion, useScroll, useTransform } from "framer-motion";
import { useRef, useState, useEffect } from "react";
import {
  Bot,
  Shield,
  Brain,
  Navigation,
  Users,
  Clock,
  ChevronRight,
  Sparkles,
  Heart,
  GraduationCap,
  Building2,
  Leaf,
  Target,
  Zap,
  Quote,
  ArrowRight,
  Play,
  Pause,
  Volume2,
  Eye,
  Cpu,
  Radio,
} from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "Neural Recognition",
    description: "98.7% accuracy face recognition with emotion detection and behavioral analysis.",
    stat: "2ms",
    statLabel: "Response"
  },
  {
    icon: Navigation,
    title: "Spatial Awareness",
    description: "LiDAR + stereo vision for centimeter-precise navigation in dynamic environments.",
    stat: "±2cm",
    statLabel: "Precision"
  },
  {
    icon: Shield,
    title: "Zero-Trust Security",
    description: "On-device encryption, SOC2 certified, HIPAA & GDPR compliant architecture.",
    stat: "256bit",
    statLabel: "Encryption"
  },
  {
    icon: Users,
    title: "Adaptive Interaction",
    description: "Context-aware responses that adjust tone, pace, and complexity per individual.",
    stat: "20+",
    statLabel: "Languages"
  },
  {
    icon: Clock,
    title: "Perpetual Operation",
    description: "Intelligent power management with predictive charging and hot-swap batteries.",
    stat: "24h",
    statLabel: "Uptime"
  },
  {
    icon: Zap,
    title: "Edge Computing",
    description: "On-device AI processing with cloud sync for fleet learning and updates.",
    stat: "50ms",
    statLabel: "Latency"
  },
];

const sdgGoals = [
  {
    number: 3,
    title: "Health & Wellbeing",
    description: "24/7 patient monitoring, medication reminders, and companionship for elderly care.",
    icon: Heart,
    gradient: "from-rose-500 to-pink-600",
  },
  {
    number: 4,
    title: "Quality Education",
    description: "Interactive tutoring, attendance automation, and personalized learning support.",
    icon: GraduationCap,
    gradient: "from-amber-500 to-orange-600",
  },
  {
    number: 9,
    title: "Innovation & Infrastructure",
    description: "Democratizing robotics access for institutions of all sizes.",
    icon: Building2,
    gradient: "from-violet-500 to-purple-600",
  },
  {
    number: 11,
    title: "Sustainable Communities",
    description: "Energy-efficient operations, recyclable components, carbon-neutral manufacturing.",
    icon: Leaf,
    gradient: "from-emerald-500 to-green-600",
  },
];

const testimonials = [
  {
    quote: "The elderly residents don't see FARS as a machine - they see a companion. That emotional connection is invaluable.",
    author: "Dr. Amanda Foster",
    role: "Director, Sunrise Senior Living",
    avatar: "AF",
  },
  {
    quote: "Implementation took 3 days. The ROI was visible within the first month through reduced administrative overhead.",
    author: "Michael Chang",
    role: "CTO, Metro General Hospital",
    avatar: "MC",
  },
  {
    quote: "Our students are more engaged than ever. FARS makes learning feel like the future - because it is.",
    author: "Principal Sarah Mitchell",
    role: "Greenwood Academy",
    avatar: "SM",
  },
];

const stats = [
  { value: "500+", label: "Units Active", icon: Bot },
  { value: "98.7%", label: "System Uptime", icon: Radio },
  { value: "50K+", label: "Daily Interactions", icon: Users },
  { value: "<50ms", label: "Response Time", icon: Zap },
];

const capabilities = [
  { icon: Eye, label: "Vision" },
  { icon: Volume2, label: "Voice" },
  { icon: Brain, label: "Cognition" },
  { icon: Navigation, label: "Mobility" },
  { icon: Cpu, label: "Processing" },
  { icon: Shield, label: "Security" },
];

export default function Home() {
  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"]
  });
  const heroOpacity = useTransform(scrollYProgress, [0, 1], [1, 0]);
  const heroScale = useTransform(scrollYProgress, [0, 1], [1, 0.8]);
  
  const [activeCapability, setActiveCapability] = useState(0);
  
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveCapability((prev) => (prev + 1) % capabilities.length);
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-background overflow-x-hidden">
      <Navbar />

      <section ref={heroRef} className="relative min-h-screen flex items-center justify-center">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-primary/5 via-background to-background" />
          <svg className="absolute inset-0 w-full h-full opacity-[0.03]" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="grid" width="60" height="60" patternUnits="userSpaceOnUse">
                <path d="M 60 0 L 0 0 0 60" fill="none" stroke="currentColor" strokeWidth="1"/>
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
          </svg>
          <motion.div 
            className="absolute top-1/3 left-1/4 w-[500px] h-[500px] rounded-full"
            style={{ 
              background: "radial-gradient(circle, rgba(0,255,136,0.08) 0%, transparent 70%)",
            }}
            animate={{ 
              scale: [1, 1.2, 1],
              opacity: [0.5, 0.8, 0.5],
            }}
            transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
          />
          <motion.div 
            className="absolute bottom-1/4 right-1/4 w-[400px] h-[400px] rounded-full"
            style={{ 
              background: "radial-gradient(circle, rgba(0,212,255,0.06) 0%, transparent 70%)",
            }}
            animate={{ 
              scale: [1.2, 1, 1.2],
              opacity: [0.3, 0.6, 0.3],
            }}
            transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
          />
        </div>

        <motion.div 
          style={{ opacity: heroOpacity, scale: heroScale }}
          className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-24"
        >
          <div className="text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-primary/30 bg-primary/5 text-primary text-sm mb-8"
            >
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
              </span>
              <span className="font-medium tracking-wide">NEXT-GEN HUMANOID ROBOTICS</span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="text-5xl sm:text-6xl lg:text-7xl font-bold leading-[1.1] mb-6 tracking-tight"
              style={{ fontFamily: "'Syne', sans-serif" }}
            >
              Machines that
              <br />
              <span className="relative">
                <span className="gradient-text">understand</span>
                <motion.span 
                  className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-primary via-cyan-400 to-primary rounded-full"
                  initial={{ scaleX: 0 }}
                  animate={{ scaleX: 1 }}
                  transition={{ duration: 0.8, delay: 0.5 }}
                />
              </span>
              {" "}humans
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="text-lg sm:text-xl text-muted-foreground mb-10 max-w-2xl mx-auto"
            >
              Enterprise-grade humanoid robots with neural recognition, 
              autonomous navigation, and adaptive intelligence for healthcare, 
              education, and business.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="flex flex-col sm:flex-row gap-4 justify-center mb-16"
            >
              <Button asChild size="lg" className="h-14 px-8 text-base rounded-full bg-primary text-primary-foreground hover:bg-primary/90 group">
                <Link href="/order">
                  Configure Robot
                  <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="h-14 px-8 text-base rounded-full border-2">
                <Link href="/docs">
                  Read Documentation
                </Link>
              </Button>
            </motion.div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, delay: 0.5 }}
              className="flex justify-center gap-8 flex-wrap"
            >
              {capabilities.map((cap, i) => (
                <motion.div
                  key={cap.label}
                  className={`flex flex-col items-center gap-2 transition-all duration-300 ${
                    activeCapability === i ? "text-primary scale-110" : "text-muted-foreground/50"
                  }`}
                >
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-300 ${
                    activeCapability === i ? "bg-primary/20" : "bg-muted/50"
                  }`}>
                    <cap.icon className="w-6 h-6" />
                  </div>
                  <span className="text-xs font-medium uppercase tracking-wider">{cap.label}</span>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </motion.div>

        <div className="absolute bottom-12 left-1/2 -translate-x-1/2">
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            className="flex flex-col items-center gap-2 text-muted-foreground/50"
          >
            <span className="text-xs uppercase tracking-widest">Scroll</span>
            <div className="w-px h-8 bg-gradient-to-b from-muted-foreground/50 to-transparent" />
          </motion.div>
        </div>
      </section>

      <section className="py-24 relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 lg:gap-8">
            {stats.map((stat, i) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="relative p-6 rounded-2xl border border-border/50 bg-card/50 backdrop-blur-sm group hover:border-primary/30 transition-colors"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <stat.icon className="w-5 h-5 text-primary" />
                  </div>
                </div>
                <div className="text-3xl sm:text-4xl font-bold mb-1" style={{ fontFamily: "'Syne', sans-serif" }}>
                  {stat.value}
                </div>
                <div className="text-sm text-muted-foreground">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section id="features" className="py-24 relative">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-card/30 to-transparent" />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="max-w-xl mb-16"
          >
            <span className="text-primary font-medium text-sm uppercase tracking-widest">Capabilities</span>
            <h2 className="text-3xl sm:text-4xl font-bold mt-4 mb-4" style={{ fontFamily: "'Syne', sans-serif" }}>
              Engineered for
              <br />
              <span className="text-muted-foreground">demanding environments</span>
            </h2>
            <p className="text-muted-foreground">
              Every component optimized for reliability, security, and seamless integration with existing workflows.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.05 }}
                className="group relative p-6 rounded-2xl border border-border/50 bg-background hover:border-primary/30 transition-all duration-300"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                    <feature.icon className="w-6 h-6 text-primary" />
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-primary" style={{ fontFamily: "'Syne', sans-serif" }}>
                      {feature.stat}
                    </div>
                    <div className="text-xs text-muted-foreground uppercase tracking-wider">
                      {feature.statLabel}
                    </div>
                  </div>
                </div>
                <h3 className="text-lg font-semibold mb-2" style={{ fontFamily: "'Syne', sans-serif" }}>
                  {feature.title}
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section id="sdg" className="py-24 relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-green-500/30 bg-green-500/5 text-green-500 text-sm mb-6">
              <Target className="w-4 h-4" />
              <span className="font-medium">UN Sustainable Development Goals</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold mb-4" style={{ fontFamily: "'Syne', sans-serif" }}>
              Technology with purpose
            </h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Every robot deployed contributes to measurable positive impact across four critical global goals.
            </p>
          </motion.div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {sdgGoals.map((goal, i) => (
              <motion.div
                key={goal.number}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="relative group"
              >
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-br opacity-0 group-hover:opacity-10 transition-opacity duration-500" 
                  style={{ background: `linear-gradient(135deg, var(--tw-gradient-stops))` }}
                />
                <div className="relative p-6 rounded-2xl border border-border/50 bg-background h-full">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${goal.gradient} flex items-center justify-center mb-4`}>
                    <goal.icon className="w-6 h-6 text-white" />
                  </div>
                  <div className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-2">
                    SDG {goal.number}
                  </div>
                  <h3 className="text-lg font-semibold mb-2" style={{ fontFamily: "'Syne', sans-serif" }}>
                    {goal.title}
                  </h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{goal.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-24 relative">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-card/30 to-transparent" />
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl sm:text-4xl font-bold mb-4" style={{ fontFamily: "'Syne', sans-serif" }}>
              What leaders say
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-6">
            {testimonials.map((testimonial, i) => (
              <motion.div
                key={testimonial.author}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="relative p-6 rounded-2xl border border-border/50 bg-background"
              >
                <div className="absolute top-6 right-6 text-6xl font-serif text-primary/10">&ldquo;</div>
                <p className="text-sm text-muted-foreground mb-6 relative z-10 leading-relaxed">
                  {testimonial.quote}
                </p>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-cyan-400 flex items-center justify-center text-xs font-bold text-primary-foreground">
                    {testimonial.avatar}
                  </div>
                  <div>
                    <div className="text-sm font-semibold">{testimonial.author}</div>
                    <div className="text-xs text-muted-foreground">{testimonial.role}</div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-24">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="relative p-8 sm:p-12 rounded-3xl overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-cyan-500/5 to-transparent" />
            <div className="absolute inset-0 border border-primary/20 rounded-3xl" />
            
            <div className="relative text-center">
              <h2 className="text-2xl sm:text-3xl font-bold mb-4" style={{ fontFamily: "'Syne', sans-serif" }}>
                Ready to deploy intelligent assistance?
              </h2>
              <p className="text-muted-foreground mb-8 max-w-lg mx-auto">
                Configure your FARS robot in minutes. Our team handles installation, training, and ongoing support.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button asChild size="lg" className="h-12 px-8 rounded-full bg-primary text-primary-foreground hover:bg-primary/90">
                  <Link href="/order">
                    Start Configuration
                    <ArrowRight className="ml-2 w-4 h-4" />
                  </Link>
                </Button>
                <Button asChild variant="outline" size="lg" className="h-12 px-8 rounded-full">
                  <Link href="/contact">
                    Talk to Sales
                  </Link>
                </Button>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
