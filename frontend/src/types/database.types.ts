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
  | Json[];

export interface Database {
  public: {
    Tables: {
      users: {
        Row: {
          id: string;
          email: string;
          first_name: string | null;
          last_name: string | null;
          avatar_url: string | null;
          subscription_tier: "free" | "pro";
          payment_customer_id: string | null;
          generation_count: number;
          current_period_generations: number;
          current_period_start: string;
          onboarding_completed: boolean;
          email_verified: boolean;
          last_login_at: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id: string;
          email: string;
          first_name?: string | null;
          last_name?: string | null;
          avatar_url?: string | null;
          subscription_tier?: "free" | "pro";
          payment_customer_id?: string | null;
          generation_count?: number;
          current_period_generations?: number;
          current_period_start?: string;
          onboarding_completed?: boolean;
          email_verified?: boolean;
          last_login_at?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          email?: string;
          first_name?: string | null;
          last_name?: string | null;
          avatar_url?: string | null;
          subscription_tier?: "free" | "pro";
          payment_customer_id?: string | null;
          generation_count?: number;
          current_period_generations?: number;
          current_period_start?: string;
          onboarding_completed?: boolean;
          email_verified?: boolean;
          last_login_at?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      projects: {
        Row: {
          id: string;
          user_id: string;
          name: string;
          description: string | null;
          prompt: string | null;
          template_id: string | null;
          html_content: string | null;
          css_content: string | null;
          js_content: string | null;
          published: boolean;
          subdomain: string | null;
          deployment_url: string | null;
          deployment_id: string | null;
          theme_settings: Json | null;
          whatsapp_number: string | null;
          favicon_url: string | null;
          generation_status: "idle" | "generating" | "completed" | "failed";
          generation_error: string | null;
          last_generated_at: string | null;
          last_deployed_at: string | null;
          deleted_at: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          name: string;
          description?: string | null;
          prompt?: string | null;
          template_id?: string | null;
          html_content?: string | null;
          css_content?: string | null;
          js_content?: string | null;
          published?: boolean;
          subdomain?: string | null;
          deployment_url?: string | null;
          deployment_id?: string | null;
          theme_settings?: Json | null;
          whatsapp_number?: string | null;
          favicon_url?: string | null;
          generation_status?: "idle" | "generating" | "completed" | "failed";
          generation_error?: string | null;
          last_generated_at?: string | null;
          last_deployed_at?: string | null;
          deleted_at?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          name?: string;
          description?: string | null;
          prompt?: string | null;
          template_id?: string | null;
          html_content?: string | null;
          css_content?: string | null;
          js_content?: string | null;
          published?: boolean;
          subdomain?: string | null;
          deployment_url?: string | null;
          deployment_id?: string | null;
          theme_settings?: Json | null;
          whatsapp_number?: string | null;
          favicon_url?: string | null;
          generation_status?: "idle" | "generating" | "completed" | "failed";
          generation_error?: string | null;
          last_generated_at?: string | null;
          last_deployed_at?: string | null;
          deleted_at?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      templates: {
        Row: {
          id: string;
          user_id: string | null;
          name: string;
          description: string | null;
          preview_image: string | null;
          preview_html: string | null;
          category:
            | "business"
            | "portfolio"
            | "restaurant"
            | "services"
            | "custom"
            | null;
          base_html: string | null;
          base_css: string | null;
          base_js: string | null;
          is_system_template: boolean;
          is_active: boolean;
          is_public: boolean;
          generation_prompt: string | null;
          style_config: Json | null;
          sections_config: Json;
          content_schema: Json | null;
          tags: string[] | null;
          use_count: number;
          generation_status: "generating" | "completed" | "failed";
          generation_error: string | null;
          created_at: string;
          updated_at: string;
          created_by: string | null;
          preview_url: string | null;
        };
        Insert: {
          id?: string;
          user_id?: string | null;
          name: string;
          description?: string | null;
          preview_image?: string | null;
          preview_html?: string | null;
          category?:
            | "business"
            | "portfolio"
            | "restaurant"
            | "services"
            | "custom"
            | null;
          base_html?: string | null;
          base_css?: string | null;
          base_js?: string | null;
          is_system_template?: boolean;
          is_active?: boolean;
          is_public?: boolean;
          generation_prompt?: string | null;
          style_config?: Json | null;
          sections_config: Json;
          content_schema?: Json | null;
          tags?: string[] | null;
          use_count?: number;
          generation_status?: "generating" | "completed" | "failed";
          generation_error?: string | null;
          created_at?: string;
          updated_at?: string;
          created_by: string | null;
          preview_url: string | null;
        };
        Update: {
          id?: string;
          user_id?: string | null;
          name?: string;
          description?: string | null;
          preview_image?: string | null;
          preview_html?: string | null;
          category?:
            | "business"
            | "portfolio"
            | "restaurant"
            | "services"
            | "custom"
            | null;
          base_html?: string | null;
          base_css?: string | null;
          base_js?: string | null;
          is_system_template?: boolean;
          is_active?: boolean;
          is_public?: boolean;
          generation_prompt?: string | null;
          style_config?: Json | null;
          sections_config?: Json;
          content_schema?: Json | null;
          tags?: string[] | null;
          use_count?: number;
          generation_status?: "generating" | "completed" | "failed";
          generation_error?: string | null;
          created_at?: string;
          updated_at?: string;
          created_by: string | null;
          preview_url: string | null;
        };
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      [_ in never]: never;
    };
    Enums: {
      [_ in never]: never;
    };
  };
}

// Helper types for easier usage
export type User = Database["public"]["Tables"]["users"]["Row"];
export type Project = Database["public"]["Tables"]["projects"]["Row"];
export type Template = Database["public"]["Tables"]["templates"]["Row"];

export type UserInsert = Database["public"]["Tables"]["users"]["Insert"];
export type ProjectInsert = Database["public"]["Tables"]["projects"]["Insert"];
export type TemplateInsert =
  Database["public"]["Tables"]["templates"]["Insert"];

export type UserUpdate = Database["public"]["Tables"]["users"]["Update"];
export type ProjectUpdate = Database["public"]["Tables"]["projects"]["Update"];
export type TemplateUpdate =
  Database["public"]["Tables"]["templates"]["Update"];
