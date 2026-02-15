"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import {
  FolderOpen,
  Plus,
  Trash2,
  Loader2,
  CheckCircle2,
  ArrowRight,
  Shield,
  Eye,
  Zap,
  Brain,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

interface SourceConfig {
  id: string | null;
  path: string;
  enabled: boolean;
  exclude_patterns: string[];
}

interface SourcesConfigResponse {
  watched_directories: SourceConfig[];
  exclude_patterns: string[];
  max_file_size_mb: number;
  scan_interval_seconds: number;
  rate_limit_files_per_minute: number;
}

export default function SetupWizardPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Config state
  const [directories, setDirectories] = useState<string[]>([]);
  const [newDir, setNewDir] = useState("");
  const [excludePatterns, setExcludePatterns] = useState<string[]>([
    "node_modules",
    ".git",
    "__pycache__",
    "*.tmp",
  ]);
  const [newPattern, setNewPattern] = useState("");
  const [maxFileSize, setMaxFileSize] = useState(50);
  const [scanInterval, setScanInterval] = useState(30);
  const [rateLimit, setRateLimit] = useState(10);

  // Load existing config
  const fetchConfig = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/config/sources");
      if (response.ok) {
        const data: SourcesConfigResponse = await response.json();
        if (data.watched_directories.length > 0) {
          setDirectories(data.watched_directories.map((d) => d.path));
        }
        if (data.exclude_patterns.length > 0) {
          setExcludePatterns(data.exclude_patterns);
        }
        setMaxFileSize(data.max_file_size_mb);
        setScanInterval(data.scan_interval_seconds);
        setRateLimit(data.rate_limit_files_per_minute);
      }
    } catch {
      // Use defaults
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  const handleAddDirectory = () => {
    if (newDir.trim() && !directories.includes(newDir.trim())) {
      setDirectories([...directories, newDir.trim()]);
      setNewDir("");
    }
  };

  const handleRemoveDirectory = (dir: string) => {
    setDirectories(directories.filter((d) => d !== dir));
  };

  const handleAddPattern = () => {
    if (newPattern.trim() && !excludePatterns.includes(newPattern.trim())) {
      setExcludePatterns([...excludePatterns, newPattern.trim()]);
      setNewPattern("");
    }
  };

  const handleRemovePattern = (pattern: string) => {
    setExcludePatterns(excludePatterns.filter((p) => p !== pattern));
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const response = await fetch("/api/config/sources", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          watched_directories: directories,
          exclude_patterns: excludePatterns,
          max_file_size_mb: maxFileSize,
          scan_interval_seconds: scanInterval,
          rate_limit_files_per_minute: rateLimit,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to save configuration");
      }

      // Move to success step
      setStep(3);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  const handleFinish = () => {
    router.push("/");
  };

  // Steps
  const steps = [
    { title: "Welcome", icon: Brain },
    { title: "Directories", icon: FolderOpen },
    { title: "Settings", icon: Zap },
    { title: "Complete", icon: CheckCircle2 },
  ];

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-muted">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted p-4 md:p-8">
      <div className="max-w-2xl mx-auto">
        {/* Progress */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-2">
            {steps.map((s, idx) => {
              const Icon = s.icon;
              return (
                <div
                  key={idx}
                  className={`flex items-center ${idx < steps.length - 1 ? "flex-1" : ""}`}
                >
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
                      idx <= step
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted text-muted-foreground"
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  {idx < steps.length - 1 && (
                    <div
                      className={`h-1 flex-1 mx-2 rounded transition-colors ${
                        idx < step ? "bg-primary" : "bg-muted"
                      }`}
                    />
                  )}
                </div>
              );
            })}
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            {steps.map((s, idx) => (
              <span key={idx} className={idx <= step ? "text-foreground font-medium" : ""}>
                {s.title}
              </span>
            ))}
          </div>
        </div>

        {/* Step Content */}
        {step === 0 && (
          <Card>
            <CardHeader className="text-center">
              <div className="mx-auto mb-4 w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                <Brain className="w-8 h-8 text-primary" />
              </div>
              <CardTitle className="text-2xl">Welcome to Synapsis</CardTitle>
              <CardDescription>
                Your personal, air-gapped knowledge engine. Let&apos;s set up your memory system.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-3">
                <div className="text-center p-4 rounded-lg bg-muted">
                  <Shield className="w-6 h-6 mx-auto mb-2 text-green-600" />
                  <div className="font-medium text-sm">100% Private</div>
                  <div className="text-xs text-muted-foreground">No internet connection</div>
                </div>
                <div className="text-center p-4 rounded-lg bg-muted">
                  <Eye className="w-6 h-6 mx-auto mb-2 text-blue-600" />
                  <div className="font-medium text-sm">Zero-Touch</div>
                  <div className="text-xs text-muted-foreground">Auto-ingests your files</div>
                </div>
                <div className="text-center p-4 rounded-lg bg-muted">
                  <Zap className="w-6 h-6 mx-auto mb-2 text-amber-600" />
                  <div className="font-medium text-sm">Smart Insights</div>
                  <div className="text-xs text-muted-foreground">Discovers connections</div>
                </div>
              </div>
            </CardContent>
            <CardFooter className="justify-end">
              <Button onClick={() => setStep(1)}>
                Get Started
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </CardFooter>
          </Card>
        )}

        {step === 1 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FolderOpen className="w-5 h-5" />
                Select Directories to Watch
              </CardTitle>
              <CardDescription>
                Synapsis will automatically monitor these directories for new files. Your files are
                never modified — we only read them.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Add directory */}
              <div className="flex gap-2">
                <Input
                  placeholder="Enter directory path (e.g., C:\Users\You\Documents)"
                  value={newDir}
                  onChange={(e) => setNewDir(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleAddDirectory()}
                />
                <Button onClick={handleAddDirectory} disabled={!newDir.trim()}>
                  <Plus className="w-4 h-4" />
                </Button>
              </div>

              {/* Common suggestions */}
              <div>
                <div className="text-sm text-muted-foreground mb-2">Quick Add:</div>
                <div className="flex flex-wrap gap-2">
                  {["~/Documents", "~/Desktop", "~/Notes", "~/Downloads"].map((suggestion) => (
                    <Button
                      key={suggestion}
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const expanded = suggestion.replace("~", "C:\\Users\\" + (process?.env?.USERNAME || "User"));
                        if (!directories.includes(expanded)) {
                          setDirectories([...directories, expanded]);
                        }
                      }}
                    >
                      {suggestion}
                    </Button>
                  ))}
                </div>
              </div>

              {/* Selected directories */}
              {directories.length > 0 && (
                <div>
                  <div className="text-sm font-medium mb-2">
                    Selected Directories ({directories.length})
                  </div>
                  <div className="space-y-2">
                    {directories.map((dir) => (
                      <div
                        key={dir}
                        className="flex items-center justify-between p-2 rounded-lg bg-muted"
                      >
                        <div className="flex items-center gap-2">
                          <FolderOpen className="w-4 h-4 text-muted-foreground" />
                          <span className="text-sm truncate">{dir}</span>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleRemoveDirectory(dir)}
                        >
                          <Trash2 className="w-4 h-4 text-destructive" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {directories.length === 0 && (
                <div className="text-center py-8 text-muted-foreground">
                  <FolderOpen className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No directories selected yet.</p>
                  <p className="text-sm">Add at least one directory to continue.</p>
                </div>
              )}
            </CardContent>
            <CardFooter className="justify-between">
              <Button variant="outline" onClick={() => setStep(0)}>
                <ChevronLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <Button onClick={() => setStep(2)} disabled={directories.length === 0}>
                Continue
                <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
            </CardFooter>
          </Card>
        )}

        {step === 2 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5" />
                Configure Settings
              </CardTitle>
              <CardDescription>
                Fine-tune how Synapsis processes your files. These defaults work well for most users.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Exclude patterns */}
              <div>
                <Label className="mb-2 block">Exclude Patterns</Label>
                <div className="flex gap-2 mb-2">
                  <Input
                    placeholder="Add pattern (e.g., *.log)"
                    value={newPattern}
                    onChange={(e) => setNewPattern(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleAddPattern()}
                  />
                  <Button onClick={handleAddPattern} disabled={!newPattern.trim()}>
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-1">
                  {excludePatterns.map((pattern) => (
                    <Badge
                      key={pattern}
                      variant="secondary"
                      className="cursor-pointer"
                      onClick={() => handleRemovePattern(pattern)}
                    >
                      {pattern}
                      <Trash2 className="w-3 h-3 ml-1" />
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Max file size */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label>Max File Size</Label>
                  <span className="text-sm text-muted-foreground">{maxFileSize} MB</span>
                </div>
                <Slider
                  value={[maxFileSize]}
                  onValueChange={([v]) => setMaxFileSize(v)}
                  min={1}
                  max={200}
                  step={1}
                />
              </div>

              {/* Scan interval */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label>Scan Interval</Label>
                  <span className="text-sm text-muted-foreground">{scanInterval} seconds</span>
                </div>
                <Slider
                  value={[scanInterval]}
                  onValueChange={([v]) => setScanInterval(v)}
                  min={10}
                  max={300}
                  step={10}
                />
              </div>

              {/* Rate limit */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label>Rate Limit</Label>
                  <span className="text-sm text-muted-foreground">{rateLimit} files/min</span>
                </div>
                <Slider
                  value={[rateLimit]}
                  onValueChange={([v]) => setRateLimit(v)}
                  min={1}
                  max={50}
                  step={1}
                />
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
                  {error}
                </div>
              )}
            </CardContent>
            <CardFooter className="justify-between">
              <Button variant="outline" onClick={() => setStep(1)}>
                <ChevronLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <Button onClick={handleSave} disabled={saving}>
                {saving ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    Save & Finish
                    <CheckCircle2 className="w-4 h-4 ml-2" />
                  </>
                )}
              </Button>
            </CardFooter>
          </Card>
        )}

        {step === 3 && (
          <Card>
            <CardHeader className="text-center">
              <div className="mx-auto mb-4 w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                <CheckCircle2 className="w-8 h-8 text-green-600" />
              </div>
              <CardTitle className="text-2xl">Setup Complete!</CardTitle>
              <CardDescription>
                Synapsis is now configured and ready to use. Your files will be automatically
                ingested in the background.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="rounded-lg bg-muted p-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Directories watching:</span>
                  <span className="font-medium">{directories.length}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Exclude patterns:</span>
                  <span className="font-medium">{excludePatterns.length}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Max file size:</span>
                  <span className="font-medium">{maxFileSize} MB</span>
                </div>
              </div>

              <div className="text-center text-sm text-muted-foreground">
                You can change these settings anytime from the sidebar.
              </div>
            </CardContent>
            <CardFooter className="justify-center">
              <Button onClick={handleFinish} size="lg">
                Start Using Synapsis
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </CardFooter>
          </Card>
        )}
      </div>
    </div>
  );
}
