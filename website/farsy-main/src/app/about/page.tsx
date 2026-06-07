"use client";

import { motion } from "framer-motion";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import {
  Bot,
  Target,
  Users,
  Award,
  Rocket,
  Heart,
  GraduationCap,
  Building2,
  Globe,
  Linkedin,
  Twitter,
} from "lucide-react";

const team = [
  { name: "Arjun Mehta", role: "CEO & Founder", image: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=200&h=200&fit=crop&crop=face" },
  { name: "Priya Sharma", role: "CTO", image: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200&h=200&fit=crop&crop=face" },
  { name: "Rahul Patel", role: "Head of AI", image: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=200&h=200&fit=crop&crop=face" },
  { name: "Ananya Reddy", role: "Head of Design", image: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=200&h=200&fit=crop&crop=face" },
];

const milestones = [
  { year: "2021", title: "Founded", description: "Started as a university research project" },
  { year: "2022", title: "First Prototype", description: "Developed working humanoid robot prototype" },
  { year: "2023", title: "Seed Funding", description: "Raised $2M from leading VCs" },
  { year: "2024", title: "Commercial Launch", description: "Deployed first 100 robots across India" },
  { year: "2025", title: "Global Expansion", description: "Expanding to Southeast Asia & Americas" },
];

const values = [
  { icon: Heart, title: "Human-Centered", description: "Technology that enhances human capability, not replaces it" },
  { icon: Target, title: "Purpose-Driven", description: "Every feature serves a real-world need" },
  { icon: Award, title: "Excellence", description: "Uncompromising quality in everything we build" },
  { icon: Globe, title: "Accessibility", description: "Making advanced robotics accessible to all" },
];

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />

      <section className="pt-28 pb-16 px-4">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-16"
          >
            <h1 className="text-4xl sm:text-5xl font-bold mb-6" style={{ fontFamily: "'Syne', sans-serif" }}>
              Building the Future of <span className="gradient-text">Human-Robot Interaction</span>
            </h1>
            <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
              FARS was born from a simple belief: intelligent robotics should enhance human lives, 
              making healthcare more compassionate, education more engaging, and workplaces more efficient.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 gap-12 items-center mb-24">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
            >
              <h2 className="text-3xl font-bold mb-6" style={{ fontFamily: "'Syne', sans-serif" }}>
                Our Story
              </h2>
              <div className="space-y-4 text-muted-foreground">
                <p>
                  What started as a university robotics project in Bangalore has grown into a mission to transform 
                  how institutions interact with automation. We saw firsthand how hospitals struggled with staff 
                  shortages, schools needed engaging ways to connect with students, and businesses sought 
                  smarter ways to operate.
                </p>
                <p>
                  Our founding team combined expertise in AI, mechanical engineering, and human-computer 
                  interaction to create FARS - robots that don&apos;t just perform tasks, but understand context, 
                  recognize individuals, and adapt to their environment.
                </p>
                <p>
                  Today, FARS robots serve hospitals, schools, and businesses across India, with plans to 
                  expand globally. But our mission remains the same: making intelligent assistance accessible 
                  to everyone.
                </p>
              </div>
            </motion.div>
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="relative"
            >
              <div className="aspect-video rounded-2xl overflow-hidden">
                <img
                  src="https://images.unsplash.com/photo-1531746790731-6c087fecd65a?w=800&h=450&fit=crop"
                  alt="Team working on robot"
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="absolute -bottom-6 -right-6 p-4 rounded-xl glass-panel">
                <div className="text-3xl font-bold text-primary" style={{ fontFamily: "'Syne', sans-serif" }}>500+</div>
                <div className="text-sm text-muted-foreground">Robots Deployed</div>
              </div>
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-24"
          >
            <h2 className="text-3xl font-bold text-center mb-12" style={{ fontFamily: "'Syne', sans-serif" }}>
              Our Values
            </h2>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {values.map((value, i) => (
                <motion.div
                  key={value.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                  className="p-6 rounded-2xl bg-card border border-border text-center"
                >
                  <div className="w-12 h-12 mx-auto rounded-xl bg-primary/10 flex items-center justify-center mb-4">
                    <value.icon className="w-6 h-6 text-primary" />
                  </div>
                  <h3 className="font-bold mb-2" style={{ fontFamily: "'Syne', sans-serif" }}>{value.title}</h3>
                  <p className="text-sm text-muted-foreground">{value.description}</p>
                </motion.div>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-24"
          >
            <h2 className="text-3xl font-bold text-center mb-12" style={{ fontFamily: "'Syne', sans-serif" }}>
              Our Journey
            </h2>
            <div className="relative">
              <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-border -translate-x-1/2 hidden md:block" />
              <div className="space-y-8">
                {milestones.map((milestone, i) => (
                  <motion.div
                    key={milestone.year}
                    initial={{ opacity: 0, x: i % 2 === 0 ? -20 : 20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    viewport={{ once: true }}
                    className={`relative flex flex-col md:flex-row gap-4 ${
                      i % 2 === 0 ? "md:flex-row-reverse md:text-right" : ""
                    }`}
                  >
                    <div className="flex-1" />
                    <div className="hidden md:flex w-12 h-12 rounded-full bg-primary text-primary-foreground items-center justify-center font-bold z-10">
                      {milestone.year.slice(2)}
                    </div>
                    <div className="flex-1 p-6 rounded-2xl bg-card border border-border">
                      <div className="text-primary font-bold md:hidden">{milestone.year}</div>
                      <h3 className="font-bold mb-1" style={{ fontFamily: "'Syne', sans-serif" }}>{milestone.title}</h3>
                      <p className="text-sm text-muted-foreground">{milestone.description}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-24"
          >
            <h2 className="text-3xl font-bold text-center mb-4" style={{ fontFamily: "'Syne', sans-serif" }}>
              Leadership Team
            </h2>
            <p className="text-center text-muted-foreground mb-12 max-w-xl mx-auto">
              Passionate engineers and innovators united by a vision of accessible robotics.
            </p>
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {team.map((member, i) => (
                <motion.div
                  key={member.name}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                  className="p-6 rounded-2xl bg-card border border-border text-center group"
                >
                  <div className="w-24 h-24 mx-auto rounded-full overflow-hidden mb-4">
                    <img src={member.image} alt={member.name} className="w-full h-full object-cover" />
                  </div>
                  <h3 className="font-bold" style={{ fontFamily: "'Syne', sans-serif" }}>{member.name}</h3>
                  <p className="text-sm text-muted-foreground mb-4">{member.role}</p>
                  <div className="flex justify-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <a href="#" className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center hover:bg-primary/20 transition-colors">
                      <Linkedin className="w-4 h-4 text-primary" />
                    </a>
                    <a href="#" className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center hover:bg-primary/20 transition-colors">
                      <Twitter className="w-4 h-4 text-primary" />
                    </a>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="p-8 sm:p-12 rounded-3xl bg-gradient-to-br from-primary/20 via-cyan-500/10 to-primary/5 text-center"
          >
            <h2 className="text-2xl sm:text-3xl font-bold mb-4" style={{ fontFamily: "'Syne', sans-serif" }}>
              Join Our Mission
            </h2>
            <p className="text-muted-foreground mb-8 max-w-xl mx-auto">
              We&apos;re always looking for talented individuals who share our passion for robotics and human-centered technology.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button asChild size="lg" className="rounded-full">
                <Link href="/contact">
                  Get in Touch
                  <Rocket className="w-4 h-4 ml-2" />
                </Link>
              </Button>
              <Button asChild variant="outline" size="lg" className="rounded-full">
                <Link href="/order">Order a Robot</Link>
              </Button>
            </div>
          </motion.div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
