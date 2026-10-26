import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://myqahjpudksndhgswdjf.supabase.co';
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im15cWFoanB1ZGtzbmRoZ3N3ZGpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTIzODc3NjUsImV4cCI6MjEwNzk2Mzc2NX0.JUNzCX0_PHehgHnHPcl0EX_Mvzd4IaYgvCjwz4H2caM';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
