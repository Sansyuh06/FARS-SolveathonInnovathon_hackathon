"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import { supabase, type Order } from "@/lib/supabase";
import {
  Bot,
  Check,
  ChevronRight,
  Building2,
  User,
  Mail,
  Phone,
  MapPin,
  Package,
  Sparkles,
  Shield,
  Brain,
  Navigation,
  Users,
  Clock,
  Zap,
  MessageSquare,
  Camera,
  Volume2,
  Wifi,
  Heart,
} from "lucide-react";

const robotConfigs = [
  {
    id: "basic",
    name: "Sentinel",
    price: 15000,
    description: "Essential automation for small facilities",
    features: ["Face Recognition", "Basic Navigation", "Voice Interaction", "8-hour battery"],
    color: "#3b82f6",
  },
  {
    id: "advanced",
    name: "Guardian",
    price: 35000,
    description: "Full-featured for medium enterprises",
    features: ["Advanced AI Recognition", "LiDAR Navigation", "Multi-language Voice", "12-hour battery", "Real-time Analytics"],
    color: "#00ff88",
    popular: true,
  },
  {
    id: "enterprise",
    name: "Apex",
    price: 75000,
    description: "Maximum capability for large institutions",
    features: ["Enterprise AI Suite", "Autonomous Fleet Management", "Custom Integration API", "24-hour battery", "Priority Support", "On-site Training"],
    color: "#a855f7",
  },
];

const additionalFeatures = [
  { id: "elderly_mode", name: "Elderly Care Mode", price: 2500, icon: Heart, description: "Specialized assistance for senior care" },
  { id: "multilingual", name: "Multilingual Pack", price: 1500, icon: MessageSquare, description: "Support for 20+ languages" },
  { id: "hd_cameras", name: "HD Camera Array", price: 3000, icon: Camera, description: "360° high-definition vision" },
  { id: "premium_audio", name: "Premium Audio", price: 1000, icon: Volume2, description: "Enhanced speakers & microphones" },
  { id: "5g_module", name: "5G Connectivity", price: 2000, icon: Wifi, description: "Ultra-fast mobile connectivity" },
  { id: "extended_warranty", name: "Extended Warranty", price: 5000, icon: Shield, description: "5-year comprehensive coverage" },
];

type Step = 1 | 2 | 3 | 4;

export default function OrderPage() {
  const [step, setStep] = useState<Step>(1);
  const [selectedConfig, setSelectedConfig] = useState<string>("advanced");
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);
  const [quantity, setQuantity] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [orderComplete, setOrderComplete] = useState(false);
  
  const [formData, setFormData] = useState({
    institutionName: "",
    contactName: "",
    email: "",
    phone: "",
    address: "",
    city: "",
    country: "",
    notes: "",
  });

  const config = robotConfigs.find(c => c.id === selectedConfig)!;
  const featuresTotal = selectedFeatures.reduce((acc, id) => {
    const feature = additionalFeatures.find(f => f.id === id);
    return acc + (feature?.price || 0);
  }, 0);
  const totalPrice = (config.price + featuresTotal) * quantity;

  const toggleFeature = (id: string) => {
    setSelectedFeatures(prev => 
      prev.includes(id) ? prev.filter(f => f !== id) : [...prev, id]
    );
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const canProceed = () => {
    switch (step) {
      case 1: return selectedConfig !== "";
      case 2: return true;
      case 3: 
        return formData.institutionName && formData.contactName && 
               formData.email && formData.phone && 
               formData.address && formData.city && formData.country;
      case 4: return true;
      default: return false;
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    
    const order: Order = {
      institution_name: formData.institutionName,
      contact_name: formData.contactName,
      email: formData.email,
      phone: formData.phone,
      address: formData.address,
      city: formData.city,
      country: formData.country,
      robot_config: selectedConfig as 'basic' | 'advanced' | 'enterprise',
      features: selectedFeatures,
      quantity: quantity,
      total_price: totalPrice,
      notes: formData.notes,
    };

    const { error } = await supabase.from('orders').insert([order]);
    
    if (error) {
      toast.error("Failed to submit order. Please try again.");
      console.error(error);
    } else {
      setOrderComplete(true);
      toast.success("Order submitted successfully!");
    }
    
    setIsSubmitting(false);
  };

  if (orderComplete) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="min-h-screen flex items-center justify-center px-4 pt-24">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="max-w-lg w-full text-center"
          >
            <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-primary/20 flex items-center justify-center">
              <Check className="w-12 h-12 text-primary" />
            </div>
            <h1 className="text-3xl font-bold mb-4" style={{ fontFamily: "'Syne', sans-serif" }}>
              Order Confirmed!
            </h1>
            <p className="text-muted-foreground mb-8">
              Thank you for your order. Our team will contact you within 24 hours to confirm details and arrange delivery.
            </p>
            <div className="p-6 rounded-2xl bg-card border border-border mb-8">
              <div className="text-sm text-muted-foreground mb-2">Order Total</div>
              <div className="text-4xl font-bold text-primary" style={{ fontFamily: "'Syne', sans-serif" }}>
                ${totalPrice.toLocaleString()}
              </div>
              <div className="text-sm text-muted-foreground mt-2">
                {quantity}x {config.name} Robot{quantity > 1 ? 's' : ''}
              </div>
            </div>
            <Button asChild size="lg" className="rounded-full">
              <a href="/">Return Home</a>
            </Button>
          </motion.div>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <div className="pt-28 pb-16 px-4">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-12"
          >
            <h1 className="text-4xl sm:text-5xl font-bold mb-4" style={{ fontFamily: "'Syne', sans-serif" }}>
              Configure Your <span className="gradient-text">Robot</span>
            </h1>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Customize your FARS robot to match your institution&apos;s specific requirements.
            </p>
          </motion.div>

          <div className="flex justify-center mb-12">
            <div className="flex items-center gap-2 sm:gap-4">
              {[1, 2, 3, 4].map((s) => (
                <div key={s} className="flex items-center">
                  <button
                    onClick={() => s < step && setStep(s as Step)}
                    disabled={s > step}
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-all ${
                      s === step
                        ? "bg-primary text-primary-foreground"
                        : s < step
                        ? "bg-primary/20 text-primary cursor-pointer hover:bg-primary/30"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {s < step ? <Check className="w-5 h-5" /> : s}
                  </button>
                  {s < 4 && (
                    <div className={`w-8 sm:w-16 h-0.5 mx-1 ${s < step ? "bg-primary" : "bg-muted"}`} />
                  )}
                </div>
              ))}
            </div>
          </div>

          <AnimatePresence mode="wait">
            {step === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-8"
              >
                <h2 className="text-2xl font-bold text-center" style={{ fontFamily: "'Syne', sans-serif" }}>
                  Select Robot Configuration
                </h2>
                
                <div className="grid md:grid-cols-3 gap-6">
                  {robotConfigs.map((cfg) => (
                    <button
                      key={cfg.id}
                      onClick={() => setSelectedConfig(cfg.id)}
                      className={`relative p-6 rounded-2xl border-2 text-left transition-all ${
                        selectedConfig === cfg.id
                          ? "border-primary bg-primary/5"
                          : "border-border hover:border-primary/50"
                      }`}
                    >
                      {cfg.popular && (
                        <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-primary text-primary-foreground text-xs font-semibold">
                          Most Popular
                        </div>
                      )}
                      
                      <div
                        className="w-14 h-14 rounded-xl flex items-center justify-center mb-4"
                        style={{ backgroundColor: `${cfg.color}20` }}
                      >
                        <Bot className="w-7 h-7" style={{ color: cfg.color }} />
                      </div>
                      
                      <h3 className="text-xl font-bold mb-1" style={{ fontFamily: "'Syne', sans-serif" }}>
                        {cfg.name}
                      </h3>
                      <p className="text-sm text-muted-foreground mb-4">{cfg.description}</p>
                      
                      <div className="text-3xl font-bold mb-4" style={{ color: cfg.color }}>
                        ${cfg.price.toLocaleString()}
                      </div>
                      
                      <ul className="space-y-2">
                        {cfg.features.map((feature) => (
                          <li key={feature} className="flex items-center gap-2 text-sm">
                            <Check className="w-4 h-4 text-primary" />
                            {feature}
                          </li>
                        ))}
                      </ul>
                      
                      {selectedConfig === cfg.id && (
                        <div className="absolute top-4 right-4 w-6 h-6 rounded-full bg-primary flex items-center justify-center">
                          <Check className="w-4 h-4 text-primary-foreground" />
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}

            {step === 2 && (
              <motion.div
                key="step2"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-8"
              >
                <h2 className="text-2xl font-bold text-center" style={{ fontFamily: "'Syne', sans-serif" }}>
                  Add Optional Features
                </h2>
                
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {additionalFeatures.map((feature) => (
                    <button
                      key={feature.id}
                      onClick={() => toggleFeature(feature.id)}
                      className={`p-4 rounded-xl border-2 text-left transition-all ${
                        selectedFeatures.includes(feature.id)
                          ? "border-primary bg-primary/5"
                          : "border-border hover:border-primary/50"
                      }`}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                          <feature.icon className="w-5 h-5 text-primary" />
                        </div>
                        <Checkbox checked={selectedFeatures.includes(feature.id)} />
                      </div>
                      <h3 className="font-semibold mb-1">{feature.name}</h3>
                      <p className="text-xs text-muted-foreground mb-2">{feature.description}</p>
                      <div className="text-lg font-bold text-primary">+${feature.price.toLocaleString()}</div>
                    </button>
                  ))}
                </div>

                <div className="flex items-center justify-center gap-4 p-6 rounded-2xl bg-card border border-border">
                  <Label className="text-lg">Quantity:</Label>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => setQuantity(Math.max(1, quantity - 1))}
                      disabled={quantity <= 1}
                    >
                      -
                    </Button>
                    <span className="w-12 text-center text-2xl font-bold">{quantity}</span>
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => setQuantity(quantity + 1)}
                    >
                      +
                    </Button>
                  </div>
                </div>
              </motion.div>
            )}

            {step === 3 && (
              <motion.div
                key="step3"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="max-w-2xl mx-auto space-y-8"
              >
                <h2 className="text-2xl font-bold text-center" style={{ fontFamily: "'Syne', sans-serif" }}>
                  Delivery Information
                </h2>

                <div className="grid gap-6">
                  <div className="grid sm:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="institutionName">Institution Name *</Label>
                      <div className="relative">
                        <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                        <Input
                          id="institutionName"
                          name="institutionName"
                          placeholder="Acme Healthcare"
                          value={formData.institutionName}
                          onChange={handleInputChange}
                          className="pl-10"
                          required
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="contactName">Contact Person *</Label>
                      <div className="relative">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                        <Input
                          id="contactName"
                          name="contactName"
                          placeholder="John Smith"
                          value={formData.contactName}
                          onChange={handleInputChange}
                          className="pl-10"
                          required
                        />
                      </div>
                    </div>
                  </div>

                  <div className="grid sm:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="email">Email Address *</Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                        <Input
                          id="email"
                          name="email"
                          type="email"
                          placeholder="john@acme.com"
                          value={formData.email}
                          onChange={handleInputChange}
                          className="pl-10"
                          required
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="phone">Phone Number *</Label>
                      <div className="relative">
                        <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                        <Input
                          id="phone"
                          name="phone"
                          placeholder="+1 555 123 4567"
                          value={formData.phone}
                          onChange={handleInputChange}
                          className="pl-10"
                          required
                        />
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="address">Street Address *</Label>
                    <div className="relative">
                      <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
                      <Input
                        id="address"
                        name="address"
                        placeholder="123 Main Street"
                        value={formData.address}
                        onChange={handleInputChange}
                        className="pl-10"
                        required
                      />
                    </div>
                  </div>

                  <div className="grid sm:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="city">City *</Label>
                      <Input
                        id="city"
                        name="city"
                        placeholder="San Francisco"
                        value={formData.city}
                        onChange={handleInputChange}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="country">Country *</Label>
                      <Input
                        id="country"
                        name="country"
                        placeholder="United States"
                        value={formData.country}
                        onChange={handleInputChange}
                        required
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="notes">Additional Notes</Label>
                    <Textarea
                      id="notes"
                      name="notes"
                      placeholder="Any special requirements or instructions..."
                      value={formData.notes}
                      onChange={handleInputChange}
                      rows={4}
                    />
                  </div>
                </div>
              </motion.div>
            )}

            {step === 4 && (
              <motion.div
                key="step4"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="max-w-2xl mx-auto space-y-8"
              >
                <h2 className="text-2xl font-bold text-center" style={{ fontFamily: "'Syne', sans-serif" }}>
                  Review Your Order
                </h2>

                <div className="p-6 rounded-2xl bg-card border border-border space-y-6">
                  <div className="flex items-center gap-4 pb-6 border-b border-border">
                    <div
                      className="w-16 h-16 rounded-xl flex items-center justify-center"
                      style={{ backgroundColor: `${config.color}20` }}
                    >
                      <Bot className="w-8 h-8" style={{ color: config.color }} />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold" style={{ fontFamily: "'Syne', sans-serif" }}>
                        {config.name} Robot
                      </h3>
                      <p className="text-muted-foreground">Quantity: {quantity}</p>
                    </div>
                    <div className="ml-auto text-right">
                      <div className="text-2xl font-bold">${(config.price * quantity).toLocaleString()}</div>
                    </div>
                  </div>

                  {selectedFeatures.length > 0 && (
                    <div className="space-y-3 pb-6 border-b border-border">
                      <h4 className="font-semibold">Additional Features</h4>
                      {selectedFeatures.map(id => {
                        const feature = additionalFeatures.find(f => f.id === id)!;
                        return (
                          <div key={id} className="flex justify-between text-sm">
                            <span>{feature.name}</span>
                            <span>+${(feature.price * quantity).toLocaleString()}</span>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  <div className="space-y-3 pb-6 border-b border-border">
                    <h4 className="font-semibold">Delivery Details</h4>
                    <div className="text-sm text-muted-foreground space-y-1">
                      <p>{formData.institutionName}</p>
                      <p>{formData.contactName}</p>
                      <p>{formData.email} | {formData.phone}</p>
                      <p>{formData.address}</p>
                      <p>{formData.city}, {formData.country}</p>
                    </div>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-xl font-bold">Total</span>
                    <span className="text-3xl font-bold text-primary" style={{ fontFamily: "'Syne', sans-serif" }}>
                      ${totalPrice.toLocaleString()}
                    </span>
                  </div>
                </div>

                <p className="text-center text-sm text-muted-foreground">
                  By placing this order, you agree to our terms of service. Our team will contact you within 24 hours to finalize payment and delivery arrangements.
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="flex justify-between mt-12 max-w-2xl mx-auto">
            <Button
              variant="outline"
              onClick={() => setStep((step - 1) as Step)}
              disabled={step === 1}
              className="rounded-full"
            >
              Back
            </Button>
            
            {step < 4 ? (
              <Button
                onClick={() => setStep((step + 1) as Step)}
                disabled={!canProceed()}
                className="rounded-full"
              >
                Continue
                <ChevronRight className="w-4 h-4 ml-1" />
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="rounded-full bg-primary text-primary-foreground"
              >
                {isSubmitting ? "Submitting..." : "Place Order"}
                <Package className="w-4 h-4 ml-2" />
              </Button>
            )}
          </div>
        </div>
      </div>
      
      <Footer />
    </div>
  );
}
