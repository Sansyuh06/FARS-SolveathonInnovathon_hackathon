import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://tngiknqeloriclszqlyc.supabase.co';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRuZ2lrbnFlbG9yaWNsc3pxbHljIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYwOTM1NzUsImV4cCI6MjA4MTY2OTU3NX0.996vqYpLS8874nZhsb4h4dQpitLfQk6Q4BRDLFcuC5Q';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export interface Order {
  id?: string;
  institution_name: string;
  contact_name: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  country: string;
  robot_config: 'basic' | 'advanced' | 'enterprise';
  features: string[];
  quantity: number;
  total_price: number;
  status?: string;
  notes?: string;
  created_at?: string;
}

export interface ContactMessage {
  id?: string;
  name: string;
  email: string;
  subject: string;
  message: string;
  created_at?: string;
}
