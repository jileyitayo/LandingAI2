'use client';

import { useRef, useState } from 'react';
import { Plus, X, Loader2, ImageIcon } from 'lucide-react';
import { api } from '@/lib/api';

export interface Attachment {
  id: string;
  url: string;
  mediaType: string;
  filename: string | null;
}

interface AttachmentButtonProps {
  attachments: Attachment[];
  onAttachmentsChange: (attachments: Attachment[]) => void;
  projectId?: string;
  maxAttachments?: number;
  disabled?: boolean;
}

/**
 * '+' button that uploads images (from file, photos, or camera on mobile)
 * and renders thumbnail chips for uploaded attachments.
 */
export default function AttachmentButton({
  attachments,
  onAttachmentsChange,
  projectId,
  maxAttachments = 4,
  disabled = false,
}: AttachmentButtonProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadingCount, setUploadingCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    setError(null);

    const remaining = maxAttachments - attachments.length;
    const toUpload = Array.from(files).slice(0, remaining);
    if (toUpload.length === 0) {
      setError(`Maximum ${maxAttachments} images per message`);
      return;
    }

    setUploadingCount(toUpload.length);
    const uploaded: Attachment[] = [];
    try {
      for (const file of toUpload) {
        const result = await api.media.upload(file, { projectId });
        uploaded.push({
          id: result.id,
          url: result.public_url,
          mediaType: result.media_type,
          filename: result.original_filename,
        });
      }
      onAttachmentsChange([...attachments, ...uploaded]);
    } catch (err) {
      if (uploaded.length > 0) {
        onAttachmentsChange([...attachments, ...uploaded]);
      }
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploadingCount(0);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const removeAttachment = async (attachment: Attachment) => {
    onAttachmentsChange(attachments.filter((a) => a.id !== attachment.id));
    try {
      await api.media.delete(attachment.id);
    } catch {
      // Removing the chip is what matters; orphaned uploads are harmless
    }
  };

  return (
    <div className="flex flex-col gap-1.5">
      {(attachments.length > 0 || uploadingCount > 0) && (
        <div className="flex flex-wrap gap-1.5">
          {attachments.map((attachment) => (
            <div
              key={attachment.id}
              className="group relative h-12 w-12 overflow-hidden rounded-md border border-border"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={attachment.url}
                alt={attachment.filename ?? 'attachment'}
                className="h-full w-full object-cover"
              />
              <button
                type="button"
                onClick={() => removeAttachment(attachment)}
                className="absolute right-0 top-0 hidden rounded-bl-md bg-black/60 p-0.5 text-white group-hover:block"
                aria-label="Remove attachment"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
          {uploadingCount > 0 &&
            Array.from({ length: uploadingCount }).map((_, i) => (
              <div
                key={`uploading-${i}`}
                className="flex h-12 w-12 items-center justify-center rounded-md border border-dashed border-border bg-card-muted"
              >
                <Loader2 className="h-4 w-4 animate-spin text-muted" />
              </div>
            ))}
        </div>
      )}

      {error && (
        <p className="flex items-center gap-1 text-xs text-red-500">
          <ImageIcon className="h-3 w-3" />
          {error}
        </p>
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept="image/png,image/jpeg,image/webp,image/gif"
        multiple
        capture={undefined}
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
      <button
        type="button"
        onClick={() => fileInputRef.current?.click()}
        disabled={disabled || uploadingCount > 0 || attachments.length >= maxAttachments}
        className="flex h-8 w-8 items-center justify-center rounded-full border border-border text-muted transition-colors hover:border-brand/40 hover:text-fg disabled:cursor-not-allowed disabled:opacity-40"
        aria-label="Attach images"
        title="Attach images"
      >
        <Plus className="h-4 w-4" />
      </button>
    </div>
  );
}
