"use client";

import { useState, useRef } from "react";
import { api, ApiError } from "@/lib/api";
import { User } from "lucide-react";

interface UserProfile {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  avatar_url: string | null;
  subscription_tier: string;
  generation_count: number;
  current_period_generations: number;
  email_verified: boolean;
  created_at: string;
  updated_at: string;
}

interface ProfileFormProps {
  initialProfile: UserProfile;
  onUpdate: (profile: UserProfile) => void;
}

export default function ProfileForm({
  initialProfile,
  onUpdate,
}: ProfileFormProps) {
  const [firstName, setFirstName] = useState(initialProfile.first_name || "");
  const [lastName, setLastName] = useState(initialProfile.last_name || "");
  const [avatarUrl, setAvatarUrl] = useState(initialProfile.avatar_url);
  const [isUpdating, setIsUpdating] = useState(false);
  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsUpdating(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const updatedProfile = await api.users.updateProfile({
        first_name: firstName || undefined,
        last_name: lastName || undefined,
      });

      onUpdate(updatedProfile);
      setSuccessMessage("Profile updated successfully!");
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to update profile. Please try again.");
      }
    } finally {
      setIsUpdating(false);
    }
  };

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    const allowedTypes = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"];
    if (!allowedTypes.includes(file.type)) {
      setError("Invalid file type. Please upload an image (JPG, PNG, GIF, or WebP).");
      return;
    }

    // Validate file size (5MB max)
    const maxSize = 5 * 1024 * 1024; // 5MB in bytes
    if (file.size > maxSize) {
      setError("File size exceeds 5MB. Please upload a smaller image.");
      return;
    }

    setIsUploadingAvatar(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await api.users.uploadAvatar(file);
      setAvatarUrl(response.avatar_url);
      setSuccessMessage("Avatar uploaded successfully!");

      // Update parent component with new avatar URL
      const updatedProfile = { ...initialProfile, avatar_url: response.avatar_url };
      onUpdate(updatedProfile);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Failed to upload avatar. Please try again.");
      }
    } finally {
      setIsUploadingAvatar(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="card p-6">
      <h2 className="text-xl font-semibold text-fg mb-4">Profile</h2>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 dark:bg-red-500/10 dark:border-red-500/30 rounded-md">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      {/* Success Message */}
      {successMessage && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 dark:bg-green-500/10 dark:border-green-500/30 rounded-md">
          <p className="text-sm text-green-600 dark:text-green-400">{successMessage}</p>
        </div>
      )}

      {/* Avatar Upload Section */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-fg mb-2">
          Profile Picture
        </label>
        <div className="flex items-center gap-4">
          {/* Avatar Display */}
          <div className="relative">
            <div className="w-24 h-24 rounded-full bg-card-muted overflow-hidden flex items-center justify-center">
              {avatarUrl ? (
                <img
                  src={avatarUrl}
                  alt="Profile avatar"
                  className="w-full h-full object-cover"
                />
              ) : (
                <User className="w-12 h-12 text-muted" aria-hidden="true" />
              )}
            </div>
            {isUploadingAvatar && (
              <div className="absolute inset-0 bg-black bg-opacity-50 rounded-full flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
              </div>
            )}
          </div>

          {/* Upload Button */}
          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/jpg,image/png,image/gif,image/webp"
              onChange={handleAvatarUpload}
              className="hidden"
              disabled={isUploadingAvatar}
            />
            <button
              type="button"
              onClick={triggerFileInput}
              disabled={isUploadingAvatar}
              className="px-4 py-2 text-sm font-medium text-fg bg-card border border-border rounded-full hover:bg-card-muted focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/40 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isUploadingAvatar ? "Uploading..." : "Change Avatar"}
            </button>
            <p className="mt-2 text-xs text-muted">
              JPG, PNG, GIF or WebP. Max 5MB.
            </p>
          </div>
        </div>
      </div>

      {/* Profile Form */}
      <form onSubmit={handleSubmit}>
        {/* Email (Read-only) */}
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-1">
            <label htmlFor="email" className="text-sm font-medium text-fg">
              Email Address
            </label>
            <span
              className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                initialProfile.email_verified
                  ? "bg-green-100 text-green-800 dark:bg-green-500/15 dark:text-green-400"
                  : "bg-yellow-100 text-yellow-800 dark:bg-yellow-500/15 dark:text-yellow-400"
              }`}
            >
              {initialProfile.email_verified ? "Verified" : "Not Verified"}
            </span>
          </div>
          <input
            type="email"
            id="email"
            value={initialProfile.email}
            disabled
            className="w-full px-3 py-2 border border-border rounded-xl bg-card-muted text-muted cursor-not-allowed"
          />
          <p className="mt-1 text-xs text-muted">
            Email cannot be changed directly. Contact support if needed.
          </p>
        </div>

        {/* First Name */}
        <div className="mb-4">
          <label
            htmlFor="firstName"
            className="block text-sm font-medium text-fg mb-1"
          >
            First Name
          </label>
          <input
            type="text"
            id="firstName"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            className="input"
            placeholder="Enter your first name"
          />
        </div>

        {/* Last Name */}
        <div className="mb-6">
          <label
            htmlFor="lastName"
            className="block text-sm font-medium text-fg mb-1"
          >
            Last Name
          </label>
          <input
            type="text"
            id="lastName"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            className="input"
            placeholder="Enter your last name"
          />
        </div>

        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isUpdating}
            className="px-6 py-2 text-sm font-medium text-brand-fg bg-brand-gradient rounded-full shadow-glow-sm hover:shadow-glow focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60 disabled:opacity-50 disabled:shadow-none disabled:cursor-not-allowed transition-all"
          >
            {isUpdating ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </form>

      <p className="mt-6 pt-4 border-t border-border text-xs text-muted">
        Member since{" "}
        {new Date(initialProfile.created_at).toLocaleDateString("en-US", {
          month: "long",
          year: "numeric",
        })}
      </p>
    </div>
  );
}

