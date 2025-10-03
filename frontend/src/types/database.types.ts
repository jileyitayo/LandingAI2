/**
 * Database schema types for Supabase
 * Generated based on the PRD schema requirements
 */

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      users: {
        Row: {
          id: string
          email: string
          first_name: string | null
          last_name: string | null
          avatar_url: string | null
          subscription_tier: 'free' | 'pro'
          payment_customer_id: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id: string
          email: string
          first_name?: string | null
          last_name?: string | null
          avatar_url?: string | null
          subscription_tier?: 'free' | 'pro'
          payment_customer_id?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          email?: string
          first_name?: string | null
          last_name?: string | null
          avatar_url?: string | null
          subscription_tier?: 'free' | 'pro'
          payment_customer_id?: string | null
          created_at?: string
          updated_at?: string
        }
      }
      projects: {
        Row: {
          id: string
          user_id: string
          name: string
          prompt: string | null
          template_id: string | null
          html_content: string | null
          css_content: string | null
          js_content: string | null
          published: boolean
          subdomain: string | null
          deployment_url: string | null
          theme_settings: Json | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          name: string
          prompt?: string | null
          template_id?: string | null
          html_content?: string | null
          css_content?: string | null
          js_content?: string | null
          published?: boolean
          subdomain?: string | null
          deployment_url?: string | null
          theme_settings?: Json | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          name?: string
          prompt?: string | null
          template_id?: string | null
          html_content?: string | null
          css_content?: string | null
          js_content?: string | null
          published?: boolean
          subdomain?: string | null
          deployment_url?: string | null
          theme_settings?: Json | null
          created_at?: string
          updated_at?: string
        }
      }
      templates: {
        Row: {
          id: string
          name: string
          description: string | null
          preview_image: string | null
          category: string | null
          base_html: string | null
          base_css: string | null
          created_at: string
        }
        Insert: {
          id?: string
          name: string
          description?: string | null
          preview_image?: string | null
          category?: string | null
          base_html?: string | null
          base_css?: string | null
          created_at?: string
        }
        Update: {
          id?: string
          name?: string
          description?: string | null
          preview_image?: string | null
          category?: string | null
          base_html?: string | null
          base_css?: string | null
          created_at?: string
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
  }
}

// Helper types for easier usage
export type User = Database['public']['Tables']['users']['Row']
export type Project = Database['public']['Tables']['projects']['Row']
export type Template = Database['public']['Tables']['templates']['Row']

export type UserInsert = Database['public']['Tables']['users']['Insert']
export type ProjectInsert = Database['public']['Tables']['projects']['Insert']
export type TemplateInsert = Database['public']['Tables']['templates']['Insert']

export type UserUpdate = Database['public']['Tables']['users']['Update']
export type ProjectUpdate = Database['public']['Tables']['projects']['Update']
export type TemplateUpdate = Database['public']['Tables']['templates']['Update']

