'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api, DomainStatus } from '@/lib/api';
import {
  Link2, Loader2, Check, Copy, Trash2, Lock, RefreshCw, ExternalLink,
} from 'lucide-react';

// Mirrors the backend validator (routers/domains.py); server is authoritative
const DOMAIN_REGEX = /^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$/;

const POLL_FAST_MS = 5_000;
const POLL_SLOW_MS = 15_000;
const POLL_FAST_WINDOW_MS = 120_000;

interface CustomDomainCardProps {
  projectId: string;
  published: boolean;
}

function StatusBadge({ status }: { status: DomainStatus['status'] }) {
  if (status === 'verified') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:text-green-300 dark:bg-green-500/15 dark:text-green-400">
        <Check className="w-3 h-3" />
        Connected
      </span>
    );
  }
  if (status === 'error') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-500/15 dark:text-red-400">
        Error
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800 dark:text-amber-300 dark:bg-amber-500/15 dark:text-amber-400">
      <Loader2 className="w-3 h-3 animate-spin" />
      Waiting for DNS
    </span>
  );
}

export default function CustomDomainCard({ projectId, published }: CustomDomainCardProps) {
  const [tierName, setTierName] = useState<string | null>(null);
  const [domainStatus, setDomainStatus] = useState<DomainStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [input, setInput] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [removing, setRemoving] = useState(false);
  const [checking, setChecking] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [copiedValue, setCopiedValue] = useState<string | null>(null);

  // Initial load: tier + current domain status in parallel
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [profile, status] = await Promise.all([
          api.users.getProfile(),
          api.domains.getStatus(projectId),
        ]);
        if (cancelled) return;
        setTierName(profile.subscription?.tier?.tier_name || profile.subscription_tier || 'free');
        setDomainStatus(status);
      } catch {
        if (!cancelled) setTierName('free');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  // Poll while waiting for DNS (fast for the first 2 minutes, then slower)
  useEffect(() => {
    if (!domainStatus?.domain || domainStatus.status !== 'pending_dns' || !published) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    let elapsed = 0;

    const schedule = () => {
      const delay = elapsed < POLL_FAST_WINDOW_MS ? POLL_FAST_MS : POLL_SLOW_MS;
      timer = setTimeout(async () => {
        elapsed += delay;
        try {
          const next = await api.domains.getStatus(projectId);
          if (cancelled) return;
          setDomainStatus(next);
          if (next.status === 'pending_dns') schedule();
        } catch {
          if (!cancelled) schedule();
        }
      }, delay);
    };

    schedule();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [projectId, published, domainStatus?.domain, domainStatus?.status]);

  const handleConnect = async () => {
    const domain = input.trim().toLowerCase().replace(/^https?:\/\//, '').replace(/\/.*$/, '');
    if (!DOMAIN_REGEX.test(domain)) {
      setActionError("That doesn't look like a valid domain name (e.g. example.com)");
      return;
    }
    setSubmitting(true);
    setActionError(null);
    try {
      const result = await api.domains.set(projectId, domain);
      setDomainStatus(result);
      setInput('');
    } catch (err: any) {
      setActionError(err.message || 'Failed to connect domain');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRemove = async () => {
    if (!confirm(`Disconnect ${domainStatus?.domain}? Your site will stay live on its default URL.`)) return;
    setRemoving(true);
    setActionError(null);
    try {
      await api.domains.remove(projectId);
      setDomainStatus({
        domain: null,
        status: null,
        verified: false,
        misconfigured: false,
        dns_instructions: [],
        error: null,
        checked_at: null,
      });
    } catch (err: any) {
      setActionError(err.message || 'Failed to remove domain');
    } finally {
      setRemoving(false);
    }
  };

  const handleRecheck = async () => {
    setChecking(true);
    setActionError(null);
    try {
      setDomainStatus(await api.domains.getStatus(projectId));
    } catch (err: any) {
      setActionError(err.message || 'Failed to check domain status');
    } finally {
      setChecking(false);
    }
  };

  const handleCopy = async (value: string) => {
    await navigator.clipboard.writeText(value);
    setCopiedValue(value);
    setTimeout(() => setCopiedValue(null), 2000);
  };

  return (
    <div className="border-t border-border pt-4 space-y-3">
      <h3 className="flex items-center gap-2 text-sm font-semibold text-fg">
        <Link2 className="w-4 h-4 text-brand" />
        Custom Domain
      </h3>

      {loading ? (
        <div className="flex items-center gap-2 text-sm text-muted">
          <Loader2 className="w-4 h-4 animate-spin" />
          Loading…
        </div>
      ) : tierName === 'free' ? (
        <div className="flex items-start justify-between gap-4 rounded-md bg-card-muted border border-border px-4 py-3">
          <div className="flex items-start gap-2">
            <Lock className="w-4 h-4 text-muted mt-0.5" />
            <p className="text-sm text-muted">
              Connect your own domain (like <span className="font-medium">yourbusiness.com</span>) with a
              Pro plan.
            </p>
          </div>
          <Link
            href="/dashboard/profile"
            className="shrink-0 inline-flex items-center rounded-md bg-brand-gradient px-3 py-1.5 text-xs font-semibold text-white shadow-sm shadow-glow-sm hover:shadow-glow"
          >
            Upgrade to Pro
          </Link>
        </div>
      ) : !domainStatus?.domain ? (
        <div className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleConnect();
                }
              }}
              placeholder="example.com"
              disabled={!published || submitting}
              className="block w-full rounded-md border-border shadow-sm focus:border-brand focus:ring-brand/40 sm:text-sm px-3 py-2 border disabled:bg-card-muted disabled:text-muted lowercase"
            />
            <button
              type="button"
              onClick={handleConnect}
              disabled={!published || submitting || !input.trim()}
              className="shrink-0 inline-flex items-center gap-1.5 rounded-md bg-brand-gradient px-3 py-2 text-sm font-semibold text-white shadow-sm shadow-glow-sm hover:shadow-glow disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Link2 className="w-4 h-4" />}
              {submitting ? 'Connecting…' : 'Connect'}
            </button>
          </div>
          <p className="text-xs text-muted">
            {published
              ? 'Point your own domain at this site. We’ll show you the DNS records to add.'
              : 'Publish your site first, then connect a custom domain.'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center gap-2 rounded-md bg-card-muted border border-border px-3 py-2">
            {domainStatus.status === 'verified' ? (
              <a
                href={`https://${domainStatus.domain}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 truncate text-sm text-brand hover:text-brand-2"
              >
                {domainStatus.domain}
              </a>
            ) : (
              <span className="flex-1 truncate text-sm text-fg">{domainStatus.domain}</span>
            )}
            <StatusBadge status={domainStatus.status} />
            {domainStatus.status === 'verified' && (
              <a
                href={`https://${domainStatus.domain}`}
                target="_blank"
                rel="noopener noreferrer"
                className="p-1.5 text-muted hover:text-fg rounded transition-colors"
                title="Open site"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            )}
            <button
              type="button"
              onClick={handleRecheck}
              disabled={checking}
              className="p-1.5 text-muted hover:text-fg rounded transition-colors disabled:opacity-50"
              title="Check status now"
            >
              <RefreshCw className={`w-4 h-4 ${checking ? 'animate-spin' : ''}`} />
            </button>
            <button
              type="button"
              onClick={handleRemove}
              disabled={removing}
              className="p-1.5 text-muted hover:text-red-600 rounded transition-colors disabled:opacity-50"
              title="Disconnect domain"
            >
              {removing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
            </button>
          </div>

          {domainStatus.status === 'pending_dns' && domainStatus.dns_instructions.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs text-muted">
                Add these records at your DNS provider. Changes can take up to an hour to propagate.
              </p>
              <div className="overflow-x-auto rounded-md border border-border">
                <table className="min-w-full text-xs">
                  <thead className="bg-card-muted text-muted">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium">Type</th>
                      <th className="px-3 py-2 text-left font-medium">Name</th>
                      <th className="px-3 py-2 text-left font-medium">Value</th>
                      <th className="px-3 py-2" />
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {domainStatus.dns_instructions.map((record) => (
                      <tr key={`${record.type}-${record.name}-${record.value}`}>
                        <td className="px-3 py-2 font-mono text-fg">{record.type}</td>
                        <td className="px-3 py-2 font-mono text-fg">{record.name}</td>
                        <td className="px-3 py-2 font-mono text-fg break-all">{record.value}</td>
                        <td className="px-3 py-2 text-right">
                          <button
                            type="button"
                            onClick={() => handleCopy(record.value)}
                            className="p-1 text-muted hover:text-fg rounded transition-colors"
                            title="Copy value"
                          >
                            {copiedValue === record.value ? (
                              <Check className="w-3.5 h-3.5 text-green-600 dark:text-green-400" />
                            ) : (
                              <Copy className="w-3.5 h-3.5" />
                            )}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {domainStatus.error && (
            <p className="text-xs text-amber-700 dark:text-amber-400">{domainStatus.error}</p>
          )}
        </div>
      )}

      {actionError && <p className="text-xs text-red-600">{actionError}</p>}
    </div>
  );
}
