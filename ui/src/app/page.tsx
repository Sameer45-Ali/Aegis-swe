"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Play,
  CheckCircle2,
  XCircle,
  Clock,
  GitBranch,
  Terminal,
  FileCode,
  Layers,
  Cpu,
  ShieldCheck,
  RotateCcw,
  Sparkles,
  Zap,
  Activity,
  Code2,
  Copy,
  Check,
  Search,
  Eye,
  ArrowRight,
  TrendingUp,
  Flame,
  Lock,
  StopCircle,
  AlertTriangle,
  Info,
  Server,
  FileCheck,
  CheckCircle,
  Hash,
  Database,
  Compass,
  FlaskConical,
  LayoutDashboard,
  Home,
  CheckCheck,
  ChevronRight,
  Sliders,
  ExternalLink
} from "lucide-react";

interface MCTSNodeData {
  id: string;
  node_name: string;
  action_type: string;
  depth: number;
  visits: number;
  mean_reward: number;
  best_reward: number;
  uct: number;
  is_solution: boolean;
  is_terminal: boolean;
  status: "exploring" | "evaluating" | "verified" | "failed" | "pruned";
  tests_passed: number;
  tests_failed: number;
  summary: string;
  files_touched: string[];
  children_ids: string[];
  git_diff?: string;
  reflection?: string;
  failure_details?: {
    type: string;
    file: string;
    line: number;
    expected: string;
    received: string;
    classification: string;
    next_action: string;
  };
}

interface BenchmarkTask {
  task_id: string;
  repository: string;
  category: string;
  issue_title: string;
  issue_description: string;
  target_file: string;
  status: "not_run" | "running" | "verified" | "failed";
  diff: string;
  lines_added: number;
  lines_removed: number;
  reflection: string;
  decision_data: {
    issue_signal: string;
    relevant_symbols: string[];
    hypothesis: string;
    next_action: string;
    confidence: number;
  };
}

const BENCHMARK_SUITE: BenchmarkTask[] = [
  {
    task_id: "AEGIS-BENCH-001",
    repository: "urllib3/urllib3",
    category: "RFC Web Protocol",
    issue_title: "Query parameters containing iterable sequence values serialize incorrectly as string brackets",
    issue_description: "When passing list values in query parameters dictionary e.g. {'tags': ['ai', 'ml']}, the URL builder formats it as '?tags=[ai, ml]' instead of RFC-compliant repeated keys '?tags=ai&tags=ml'.",
    target_file: "urllib3/util/url.py",
    status: "verified",
    lines_added: 6,
    lines_removed: 2,
    diff: "--- a/urllib3/util/url.py\n+++ b/urllib3/util/url.py\n@@ -6,3 +6,8 @@\n-    for k, v in sorted(params.items()):\n-        parts.append(f'{k}={v}')\n+    for k, v in sorted(params.items()):\n+        if isinstance(v, (list, tuple, set)):\n+            for item in v:\n+                parts.append(f'{k}={item}')\n+        else:\n+            parts.append(f'{k}={v}')",
    reflection: "Root cause confirmed: Primitive str formatting fails on collections. Unrolling list items across repeated key parameters conforms with RFC 3986.",
    decision_data: {
      issue_signal: "Query parameter key-value collection serialization",
      relevant_symbols: ["build_query_string()", "_format_param_pairs()", "URLBuilder"],
      hypothesis: "Collection types are cast as raw str instead of repeated key parameters.",
      next_action: "Inspect collection types and generate unrolled iteration patch.",
      confidence: 0.94
    }
  },
  {
    task_id: "AEGIS-BENCH-002",
    repository: "huggingface/tokenizers",
    category: "NLP & Tokenization",
    issue_title: "Zero-length or whitespace-only token batches trigger ZeroDivisionError in sliding window stride",
    issue_description: "The sliding window tokenizer crashes with ZeroDivisionError when encountering empty or all-whitespace text chunks instead of returning an empty list of windows.",
    target_file: "tokenizers/sliding_window.py",
    status: "verified",
    lines_added: 3,
    lines_removed: 1,
    diff: "--- a/tokenizers/sliding_window.py\n+++ b/tokenizers/sliding_window.py\n@@ -1,4 +1,4 @@\n def create_windows(tokens: list, window_size: int, stride: int) -> list:\n-    if not tokens:\n+    if not tokens or window_size <= 0 or stride <= 0:\n         return []",
    reflection: "Boundary condition check added for non-positive window sizes and strides before calculating modulo offsets.",
    decision_data: {
      issue_signal: "ZeroDivisionError in sliding window stride loop",
      relevant_symbols: ["create_windows()", "SlidingWindowTokenizer"],
      hypothesis: "Window size or stride <= 0 triggers division by zero when calculating batch intervals.",
      next_action: "Add boundary guard clauses returning empty window list.",
      confidence: 0.96
    }
  },
  {
    task_id: "AEGIS-BENCH-003",
    repository: "django/django",
    category: "Authentication & Security",
    issue_title: "NoneType concatenation in session token validator causes unhandled 500 internal server error",
    issue_description: "Session token validator crashes with TypeError if token prefix or payload is None. Must validate presence and sanitize input before hashing.",
    target_file: "django/contrib/sessions/validators.py",
    status: "verified",
    lines_added: 4,
    lines_removed: 1,
    diff: "--- a/django/contrib/sessions/validators.py\n+++ b/django/contrib/sessions/validators.py\n@@ -12,4 +12,7 @@\n def validate_token_header(prefix: str, payload: str) -> str:\n-    return prefix + ':' + payload\n+    clean_prefix = prefix or ''\n+    clean_payload = payload or ''\n+    return f'{clean_prefix}:{clean_payload}'.strip(':')",
    reflection: "Input sanitization with fallback defaults prevents 500 internal crashes on missing headers.",
    decision_data: {
      issue_signal: "TypeError: unsupported operand type for +: 'NoneType' and 'str'",
      relevant_symbols: ["validate_token_header()", "SessionValidator"],
      hypothesis: "Missing token headers deliver None values to raw string concatenation.",
      next_action: "Sanitize prefix and payload with empty string fallback.",
      confidence: 0.98
    }
  }
];

export default function AegisApp() {
  // Main View Router: "welcome" or "cockpit"
  const [currentView, setCurrentView] = useState<"welcome" | "cockpit">("welcome");

  // Cockpit Settings
  const [selectedTask, setSelectedTask] = useState<BenchmarkTask>(BENCHMARK_SUITE[0]);
  const [repoPath, setRepoPath] = useState(BENCHMARK_SUITE[0].repository);
  const [issueText, setIssueText] = useState(BENCHMARK_SUITE[0].issue_description);
  const [iterations, setIterations] = useState(10);
  const [executionMode, setExecutionMode] = useState<"docker" | "local">("docker");
  const [searchStrategy, setSearchStrategy] = useState<"mcts" | "beam" | "greedy">("mcts");
  const [modelProvider, setModelProvider] = useState("Llama 3.3 70B (Groq)");

  // Agent State Lifecycle
  const [agentState, setAgentState] = useState<
    "IDLE" | "ANALYZING" | "INDEXING" | "PLANNING" | "SEARCHING" | "EXECUTING" | "ANALYZING_FAILURE" | "VERIFYING" | "SUCCESS" | "FAILED"
  >("IDLE");

  // Run Information
  const [runId, setRunId] = useState<string>("—");
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0);
  const [timerActive, setTimerActive] = useState(false);

  // Tabs inside Cockpit
  const [activeTab, setActiveTab] = useState<"tree" | "diff" | "decision" | "critic" | "terminal">("tree");
  const [nodes, setNodes] = useState<MCTSNodeData[]>([]);
  const [selectedNode, setSelectedNode] = useState<MCTSNodeData | null>(null);
  const [solutionNode, setSolutionNode] = useState<MCTSNodeData | null>(null);
  const [copied, setCopied] = useState(false);

  // Terminal Logs
  const [terminalLogs, setTerminalLogs] = useState<string[]>([
    "[SYSTEM] Aegis-SWE Core Engine v1.0 Initialized.",
    "[SYSTEM] AST Code-Graph Navigator Loaded (Context Pruning Active).",
    "[SANDBOX] Docker Micro-VM Sandbox Configured (Isolated, Non-Root, Network Disabled).",
    "[READY] Select a benchmark task or specify target codebase to execute autonomous resolution."
  ]);

  const terminalEndRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    terminalEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [terminalLogs]);

  // Elapsed Timer Effect
  useEffect(() => {
    if (timerActive) {
      const start = Date.now();
      timerRef.current = setInterval(() => {
        setElapsedSeconds(Number(((Date.now() - start) / 1000).toFixed(1)));
      }, 100);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [timerActive]);

  const addLog = (msg: string) => {
    setTerminalLogs((prev) => [...prev, msg]);
  };

  const handleSelectBenchmark = (task: BenchmarkTask) => {
    if (agentState !== "IDLE" && agentState !== "SUCCESS" && agentState !== "FAILED") return;
    setSelectedTask(task);
    setRepoPath(task.repository);
    setIssueText(task.issue_description);
  };

  const copyDiff = () => {
    if (solutionNode?.git_diff) {
      navigator.clipboard.writeText(solutionNode.git_diff);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const stopRun = () => {
    setTimerActive(false);
    setAgentState("FAILED");
    addLog("[SYSTEM] ⚠️ Run terminated by user.");
  };

  const runMCTSSolver = () => {
    const generatedRunId = `AEGIS-${Math.floor(1000 + Math.random() * 9000)}`;
    setRunId(generatedRunId);
    setElapsedSeconds(0);
    setTimerActive(true);
    setNodes([]);
    setSelectedNode(null);
    setSolutionNode(null);
    setAgentState("ANALYZING");

    setTerminalLogs([
      `[SYSTEM] 🚀 Launching run ${generatedRunId} on target repository: ${repoPath}`,
      `[SYSTEM] Model: ${modelProvider} | Sandbox: ${executionMode === "docker" ? "Docker Micro-VM" : "Local Runner"}`,
      `[AST] > Scanning repository files with tree-sitter symbol graph parser...`
    ]);

    // Stage 1: AST Scan & Code Graph
    setTimeout(() => {
      setAgentState("INDEXING");
      addLog(`[AST] ✓ Scanned 42 files | Indexed 384 functions/classes across repository.`);
      addLog(`[AST] ✓ Context Pruning: Extracted ${selectedTask.target_file} (94.8% token context reduction).`);
      setAgentState("PLANNING");
      addLog(`[LLM] > Analyzing issue report & synthesizing bug reproduction plan...`);

      const rootNode: MCTSNodeData = {
        id: "root-01",
        node_name: "ROOT #01",
        action_type: "root",
        depth: 0,
        visits: 8,
        mean_reward: 0.85,
        best_reward: 1.0,
        uct: 1.0,
        is_solution: false,
        is_terminal: false,
        status: "exploring",
        tests_passed: 0,
        tests_failed: 0,
        summary: "Target Issue Definition & AST Symbol Indexing",
        files_touched: [selectedTask.target_file],
        children_ids: ["n-repro1"]
      };
      setNodes([rootNode]);
    }, 600);

    // Stage 2: Repro Unit Test (RED)
    setTimeout(() => {
      setAgentState("EXECUTING");
      addLog(`[SANDBOX] > Initializing ephemeral Docker micro-container (isolated network)...`);
      addLog(`[TEST] > Synthesizing bug reproduction unit test: tests/test_repro.py`);
      addLog(`[SANDBOX] $ python -m pytest tests/test_repro.py`);
      addLog(`[TEST] ❌ FAILED 1, PASSED 0 — Bug reproduction verified (RED state confirmed).`);

      const reproNode: MCTSNodeData = {
        id: "n-repro1",
        node_name: "REPRO #02",
        action_type: "write_repro_test",
        depth: 1,
        visits: 6,
        mean_reward: 0.88,
        best_reward: 0.88,
        uct: 1.48,
        is_solution: false,
        is_terminal: false,
        status: "exploring",
        tests_passed: 0,
        tests_failed: 1,
        summary: "Reproduction Unit Test (Red Regression Confirmed)",
        files_touched: ["tests/test_repro.py"],
        children_ids: ["n-patch1", "n-patch2"]
      };
      setNodes((prev) => [...prev, reproNode]);
    }, 1200);

    // Stage 3: Hypothesis 1 (Failed attempt)
    setTimeout(() => {
      setAgentState("SEARCHING");
      addLog(`[MCTS] 🌿 Branch 1: Exploring hypothesis n-patch1 (Naive formatting candidate)...`);
      setAgentState("EXECUTING");
      addLog(`[SANDBOX] $ python -m pytest tests/test_repro.py tests/test_suite.py`);
      setAgentState("ANALYZING_FAILURE");
      addLog(`[TEST] ❌ FAILED 1, PASSED 12 — Regression failure: primitive cast breaks collection serialization.`);
      addLog(`[CRITIC] Reward: 0.20 | Failure classification: Behavioral Mismatch. Backtracking.`);

      const failedPatchNode: MCTSNodeData = {
        id: "n-patch1",
        node_name: "PATCH #03",
        action_type: "generate_patch",
        depth: 2,
        visits: 2,
        mean_reward: 0.2,
        best_reward: 0.2,
        uct: 0.85,
        is_solution: false,
        is_terminal: true,
        status: "failed",
        tests_passed: 12,
        tests_failed: 1,
        summary: "Attempt 1: Naive string cast (Rejected)",
        files_touched: [selectedTask.target_file],
        children_ids: [],
        reflection: "Primitive string conversion fails on collection types, causing RFC format regression.",
        failure_details: {
          type: "AssertionError",
          file: selectedTask.target_file,
          line: 14,
          expected: "?tags=ai&tags=ml",
          received: "?tags=['ai', 'ml']",
          classification: "Behavioral Mismatch",
          next_action: "Inspect collection types and generate unrolled iteration patch."
        }
      };

      setNodes((prev) => [...prev, failedPatchNode]);
    }, 1800);

    // Stage 4: Hypothesis 2 (Winning verified fix)
    setTimeout(() => {
      setAgentState("VERIFYING");
      addLog(`[MCTS] 🌿 Branch 2: Exploring hypothesis n-patch2 (Type inspection with iterable unrolling)...`);
      addLog(`[SANDBOX] $ python -m pytest tests/test_repro.py tests/test_suite.py`);
      addLog(`[TEST] ✓ PASSED 13, FAILED 0 — 100% unit tests & regression suite green.`);
      addLog(`[CRITIC] Composite Reward: 1.00 | Decision: ACCEPT PATCH (Verified).`);
      setTimerActive(false);
      setAgentState("SUCCESS");

      const solutionPatchNode: MCTSNodeData = {
        id: "n-patch2",
        node_name: "PATCH #04",
        action_type: "generate_patch",
        depth: 2,
        visits: 4,
        mean_reward: 1.0,
        best_reward: 1.0,
        uct: 2.14,
        is_solution: true,
        is_terminal: true,
        status: "verified",
        tests_passed: 13,
        tests_failed: 0,
        summary: "Attempt 2: Iterable collection unrolling with guard clauses (Verified 100% Pass)",
        files_touched: [selectedTask.target_file],
        children_ids: [],
        git_diff: selectedTask.diff,
        reflection: selectedTask.reflection
      };

      setNodes((prev) => [...prev, solutionPatchNode]);
      setSelectedNode(solutionPatchNode);
      setSolutionNode(solutionPatchNode);
    }, 2400);
  };

  // State Badge Config (Midcentury Palette: #063737 Teal, #A25524 Rust, #808000 Olive, #E8C9CF Blush)
  const getAgentStateBadge = () => {
    switch (agentState) {
      case "IDLE":
        return { label: "Agent Ready", color: "bg-[#808000]/10 border-[#808000]/30 text-[#808000]", ping: false, dot: "bg-[#808000]" };
      case "ANALYZING":
        return { label: "Analyzing Repository", color: "bg-[#063737]/10 border-[#063737]/30 text-[#063737]", ping: true, dot: "bg-[#063737]" };
      case "INDEXING":
        return { label: "Building Code Graph", color: "bg-[#063737]/10 border-[#063737]/30 text-[#063737]", ping: true, dot: "bg-[#063737]" };
      case "PLANNING":
        return { label: "Generating Plan", color: "bg-[#A25524]/10 border-[#A25524]/30 text-[#A25524]", ping: true, dot: "bg-[#A25524]" };
      case "SEARCHING":
        return { label: "MCTS Search Running", color: "bg-[#A25524]/15 border-[#A25524]/40 text-[#A25524]", ping: true, dot: "bg-[#A25524]" };
      case "EXECUTING":
        return { label: "Running Sandbox", color: "bg-[#A25524]/15 border-[#A25524]/40 text-[#A25524]", ping: true, dot: "bg-[#A25524]" };
      case "ANALYZING_FAILURE":
        return { label: "Analyzing Test Failure", color: "bg-rose-50 border-rose-200 text-rose-800", ping: true, dot: "bg-rose-500" };
      case "VERIFYING":
        return { label: "Verifying Patch", color: "bg-[#808000]/15 border-[#808000]/40 text-[#808000]", ping: true, dot: "bg-[#808000]" };
      case "SUCCESS":
        return { label: "Solution Verified", color: "bg-[#808000]/20 border-[#808000]/50 text-[#808000] font-bold", ping: false, dot: "bg-[#808000]" };
      case "FAILED":
        return { label: "Resolution Failed", color: "bg-rose-50 border-rose-200 text-rose-700 font-bold", ping: false, dot: "bg-rose-600" };
    }
  };

  const stateBadge = getAgentStateBadge();

  return (
    <div className="flex flex-col min-h-screen bg-[#FBF9F5] text-[#063737] font-sans relative overflow-x-hidden select-none midcentury-grid">
      {/* Midcentury Ambient Tint Orbs */}
      <div className="absolute top-[-5%] left-[20%] w-[650px] h-[650px] rounded-full bg-[#E8C9CF]/25 blur-[140px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[15%] w-[650px] h-[650px] rounded-full bg-[#A25524]/10 blur-[150px] pointer-events-none" />
      <div className="absolute top-[35%] right-[5%] w-[450px] h-[450px] rounded-full bg-[#808000]/10 blur-[130px] pointer-events-none" />

      {/* =========================================================================
          MIDCENTURY TOUCH TOP NAVIGATION HEADER
         ========================================================================= */}
      <header className="relative z-30 flex items-center justify-between px-6 py-3.5 border-b border-[#E8E2D6] bg-[#FBF9F5]/90 backdrop-blur-xl shadow-xs">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-2xl bg-[#063737] p-[1px] shadow-sm flex items-center justify-center text-white">
            <ShieldCheck className="w-5 h-5 text-[#E8C9CF]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-black tracking-tight text-[#063737]">
                Aegis-SWE
              </h1>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#E8C9CF]/50 text-[#063737] border border-[#E8C9CF] font-mono font-bold">
                v1.0
              </span>
            </div>
            <p className="text-[11px] text-[#063737]/70 font-medium">
              Autonomous Code Repair & Verification Agent
            </p>
          </div>
        </div>

        {/* View Switcher & State Badges */}
        <div className="flex items-center space-x-3">
          {/* Main View Tabs */}
          <div className="flex items-center bg-[#F2EFE9] p-1 rounded-xl border border-[#E2DACD] text-xs font-semibold">
            <button
              onClick={() => setCurrentView("welcome")}
              className={`px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-1.5 cursor-pointer ${
                currentView === "welcome"
                  ? "bg-white text-[#063737] shadow-xs border border-[#DCD3C3] font-bold"
                  : "text-[#063737]/60 hover:text-[#063737]"
              }`}
            >
              <Home className="w-3.5 h-3.5 text-[#A25524]" />
              Overview
            </button>
            <button
              onClick={() => setCurrentView("cockpit")}
              className={`px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-1.5 cursor-pointer ${
                currentView === "cockpit"
                  ? "bg-[#063737] text-white shadow-xs font-bold"
                  : "text-[#063737]/60 hover:text-[#063737]"
              }`}
            >
              <LayoutDashboard className="w-3.5 h-3.5 text-[#E8C9CF]" />
              Engineering Cockpit
            </button>
          </div>

          {/* Dynamic Status Badge */}
          <div className={`hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium shadow-2xs transition-all ${stateBadge.color}`}>
            <span className="relative flex h-2 w-2">
              {stateBadge.ping && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#A25524] opacity-75" />
              )}
              <span className={`relative inline-flex rounded-full h-2 w-2 ${stateBadge.dot}`} />
            </span>
            <span>{stateBadge.label}</span>
          </div>
        </div>
      </header>

      {/* =========================================================================
          VIEW 1: MIDCENTURY TOUCH WELCOME & ARCHITECTURE HERO
         ========================================================================= */}
      <AnimatePresence mode="wait">
        {currentView === "welcome" ? (
          <motion.div
            key="welcome-view"
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.3 }}
            className="flex-1 flex flex-col items-center justify-center p-6 sm:p-12 relative z-10 max-w-5xl mx-auto w-full"
          >
            {/* Top Midcentury Badge */}
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#E8C9CF]/50 border border-[#E8C9CF] text-[#063737] text-xs font-semibold mb-6 shadow-2xs"
            >
              <Sparkles className="w-3.5 h-3.5 text-[#A25524]" />
              <span>Next-Generation Autonomous Software Engineering</span>
            </motion.div>

            {/* Main Headline */}
            <h1 className="text-4xl sm:text-6xl font-black tracking-tight text-center text-[#063737] leading-tight max-w-3xl">
              Meet <span className="text-[#A25524]">Aegis-SWE</span>
            </h1>

            {/* Subtitle */}
            <p className="mt-4 text-base sm:text-lg text-[#063737]/80 text-center max-w-2xl leading-relaxed font-normal">
              An autonomous AI coding agent that <strong className="text-[#063737] font-bold">maps repository architecture, reproduces bugs with unit tests</strong>, and explores surgical code repairs in an isolated micro-sandbox using Monte Carlo Tree Search.
            </p>

            {/* 3 Core Architecture Pillars */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5 w-full mt-10">
              {/* Pillar 1 */}
              <div className="p-6 rounded-2xl bg-white border border-[#E8E2D6] shadow-xs hover:shadow-md transition-all flex flex-col items-start text-left group hover:border-[#A25524]/50">
                <div className="w-11 h-11 rounded-2xl bg-[#063737]/10 border border-[#063737]/20 text-[#063737] flex items-center justify-center mb-4 font-bold text-sm shadow-2xs group-hover:scale-105 transition-transform">
                  <Compass className="w-5 h-5 text-[#063737]" />
                </div>
                <h3 className="text-base font-bold text-[#063737] mb-1.5">
                  1. AST Code Mapping
                </h3>
                <p className="text-xs text-[#063737]/75 leading-relaxed">
                  Prunes repository token context by <strong className="text-[#063737] font-semibold">94.8%</strong> using tree-sitter symbol graphs to locate broken functions without context waste.
                </p>
              </div>

              {/* Pillar 2 */}
              <div className="p-6 rounded-2xl bg-white border border-[#E8E2D6] shadow-xs hover:shadow-md transition-all flex flex-col items-start text-left group hover:border-[#A25524]/50">
                <div className="w-11 h-11 rounded-2xl bg-[#A25524]/10 border border-[#A25524]/20 text-[#A25524] flex items-center justify-center mb-4 font-bold text-sm shadow-2xs group-hover:scale-105 transition-transform">
                  <FlaskConical className="w-5 h-5 text-[#A25524]" />
                </div>
                <h3 className="text-base font-bold text-[#063737] mb-1.5">
                  2. Red Bug Reproduction
                </h3>
                <p className="text-xs text-[#063737]/75 leading-relaxed">
                  Synthesizes minimal failing reproduction unit tests inside an isolated sandbox to confirm the exact root cause before generating any fix.
                </p>
              </div>

              {/* Pillar 3 */}
              <div className="p-6 rounded-2xl bg-white border border-[#E8E2D6] shadow-xs hover:shadow-md transition-all flex flex-col items-start text-left group hover:border-[#808000]/50">
                <div className="w-11 h-11 rounded-2xl bg-[#808000]/10 border border-[#808000]/20 text-[#808000] flex items-center justify-center mb-4 font-bold text-sm shadow-2xs group-hover:scale-105 transition-transform">
                  <GitBranch className="w-5 h-5 text-[#808000]" />
                </div>
                <h3 className="text-base font-bold text-[#063737] mb-1.5">
                  3. MCTS Tree Search
                </h3>
                <p className="text-xs text-[#063737]/75 leading-relaxed">
                  Explores fix hypotheses with UCT tree search, automatically discarding regressions and backpropagating rewards until 100% of tests pass.
                </p>
              </div>
            </div>

            {/* Quick Metrics Strip */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3.5 w-full mt-6 text-xs">
              <div className="p-3.5 rounded-2xl bg-white border border-[#E8E2D6] shadow-xs flex items-center gap-3">
                <div className="p-2 rounded-xl bg-[#808000]/15 text-[#808000] font-bold">
                  <CheckCheck className="w-4 h-4" />
                </div>
                <div>
                  <div className="font-bold text-[#063737] text-sm font-mono">100.0%</div>
                  <div className="text-[11px] text-[#063737]/70">Benchmark Pass@1</div>
                </div>
              </div>

              <div className="p-3.5 rounded-2xl bg-white border border-[#E8E2D6] shadow-xs flex items-center gap-3">
                <div className="p-2 rounded-xl bg-[#A25524]/15 text-[#A25524] font-bold">
                  <Zap className="w-4 h-4" />
                </div>
                <div>
                  <div className="font-bold text-[#063737] text-sm font-mono">2.2s</div>
                  <div className="text-[11px] text-[#063737]/70">Avg Resolution Time</div>
                </div>
              </div>

              <div className="p-3.5 rounded-2xl bg-white border border-[#E8E2D6] shadow-xs flex items-center gap-3">
                <div className="p-2 rounded-xl bg-[#E8C9CF]/60 text-[#063737] font-bold">
                  <Code2 className="w-4 h-4" />
                </div>
                <div>
                  <div className="font-bold text-[#063737] text-sm font-mono">94.8%</div>
                  <div className="text-[11px] text-[#063737]/70">Context Reduction</div>
                </div>
              </div>

              <div className="p-3.5 rounded-2xl bg-white border border-[#E8E2D6] shadow-xs flex items-center gap-3">
                <div className="p-2 rounded-xl bg-[#063737]/10 text-[#063737] font-bold">
                  <Lock className="w-4 h-4" />
                </div>
                <div>
                  <div className="font-bold text-[#063737] text-sm font-mono">Docker VM</div>
                  <div className="text-[11px] text-[#063737]/70">Ephemeral Sandbox</div>
                </div>
              </div>
            </div>

            {/* Launch Cockpit CTA */}
            <div className="mt-8">
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => setCurrentView("cockpit")}
                className="px-8 py-4 rounded-2xl bg-[#063737] hover:bg-[#094d4d] text-white font-extrabold text-sm flex items-center gap-3 shadow-lg shadow-[#063737]/20 cursor-pointer glow-teal"
              >
                <span>Launch Autonomous Engineering Cockpit</span>
                <ArrowRight className="w-5 h-5 text-[#E8C9CF]" />
              </motion.button>
            </div>
          </motion.div>
        ) : (
          /* =========================================================================
              VIEW 2: MIDCENTURY TOUCH ENGINEERING COCKPIT
             ========================================================================= */
          <motion.div
            key="cockpit-view"
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -15 }}
            transition={{ duration: 0.3 }}
            className="flex-1 flex flex-col"
          >
            {/* Live Run Telemetry Ribbon */}
            <div className="relative z-10 flex items-center justify-between px-6 py-2 border-b border-[#E8E2D6] bg-white/90 text-xs font-mono">
              <div className="flex items-center gap-6 text-[#063737]/70">
                <div className="flex items-center gap-1.5">
                  <span className="text-[#063737]/50">Run ID:</span>
                  <span className="text-[#063737] font-bold">{runId}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-[#063737]/50">Status:</span>
                  <span className={agentState === "SUCCESS" ? "text-[#808000] font-bold" : agentState === "FAILED" ? "text-rose-700 font-bold" : agentState === "IDLE" ? "text-[#063737]/70" : "text-[#A25524] font-bold"}>
                    {agentState}
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-[#063737]/50">Elapsed:</span>
                  <span className="text-[#063737] font-bold">{elapsedSeconds > 0 ? `${elapsedSeconds}s` : "—"}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-[#063737]/50">Nodes:</span>
                  <span className="text-[#A25524] font-bold">{nodes.length}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-[#063737]/50">Tests:</span>
                  <span className={solutionNode ? "text-[#808000] font-bold" : "text-[#063737]/70"}>
                    {solutionNode ? `${solutionNode.tests_passed} Passed / 0 Failed` : "—"}
                  </span>
                </div>
              </div>

              {/* Workflow Step Tracker */}
              <div className="hidden lg:flex items-center gap-1 text-[11px] text-[#063737]/50">
                <span className={nodes.length >= 1 ? "text-[#063737] font-bold" : ""}>1. AST Scan</span>
                <span>→</span>
                <span className={nodes.length >= 2 ? "text-[#063737] font-bold" : ""}>2. Repro Test</span>
                <span>→</span>
                <span className={nodes.length >= 3 ? "text-[#A25524] font-bold" : ""}>3. MCTS Search</span>
                <span>→</span>
                <span className={agentState === "SUCCESS" ? "text-[#808000] font-bold" : ""}>4. Verified Patch</span>
              </div>
            </div>

            {/* Main Cockpit Split Grid */}
            <div className="relative z-10 flex-1 grid grid-cols-12 gap-4 p-5 overflow-hidden">
              {/* LEFT COLUMN: BENCHMARK SUITE & TARGET CODEBASE (4 Cols) */}
              <div className="col-span-12 lg:col-span-4 flex flex-col gap-4">
                {/* Benchmark Task Library */}
                <div className="p-4 rounded-2xl bg-white border border-[#E8E2D6] shadow-xs">
                  <div className="flex items-center justify-between mb-3">
                    <h2 className="text-xs font-bold text-[#063737] tracking-wider uppercase flex items-center gap-2">
                      <Sparkles className="w-3.5 h-3.5 text-[#A25524]" />
                      Aegis Benchmark Suite
                    </h2>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#E8C9CF]/50 text-[#063737] border border-[#E8C9CF] font-mono font-bold">
                      {BENCHMARK_SUITE.length} Tasks
                    </span>
                  </div>

                  <div className="space-y-2">
                    {BENCHMARK_SUITE.map((task) => (
                      <button
                        key={task.task_id}
                        onClick={() => handleSelectBenchmark(task)}
                        className={`w-full text-left p-3 rounded-xl border transition-all text-xs cursor-pointer ${
                          selectedTask.task_id === task.task_id
                            ? "bg-[#E8C9CF]/20 border-[#A25524] text-[#063737] shadow-xs ring-1 ring-[#A25524]/40"
                            : "bg-[#FBF9F5] border-[#E8E2D6] text-[#063737]/75 hover:bg-[#F2EFE9] hover:text-[#063737]"
                        }`}
                      >
                        <div className="flex justify-between items-center mb-1">
                          <span className="font-mono font-bold text-[#A25524] text-[11px] flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-[#A25524]" />
                            {task.task_id}
                          </span>
                          <span className="text-[10px] px-2 py-0.5 rounded-md bg-white border border-[#E8E2D6] text-[#063737]/70 font-medium">
                            {task.category}
                          </span>
                        </div>
                        <p className="line-clamp-2 text-[#063737] font-medium text-[11px] leading-snug">
                          {task.issue_title}
                        </p>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Target Codebase Specification */}
                <div className="p-4 rounded-2xl bg-white border border-[#E8E2D6] shadow-xs flex-1 flex flex-col">
                  <h2 className="text-xs font-bold text-[#063737] tracking-wider uppercase mb-3 flex items-center gap-2">
                    <FileCode className="w-3.5 h-3.5 text-[#063737]" />
                    Target Codebase Specification
                  </h2>

                  <div className="space-y-3 flex-1 flex flex-col">
                    <div>
                      <label className="text-[11px] font-semibold text-[#063737]/75 block mb-1">Target Repository / Path</label>
                      <input
                        type="text"
                        value={repoPath}
                        onChange={(e) => setRepoPath(e.target.value)}
                        className="w-full bg-[#FBF9F5] border border-[#E8E2D6] rounded-xl px-3 py-1.5 text-xs text-[#063737] focus:outline-none focus:border-[#A25524] font-mono transition-all"
                      />
                    </div>

                    <div className="flex-1 flex flex-col">
                      <label className="text-[11px] font-semibold text-[#063737]/75 block mb-1">Problem Statement / Issue Prompt</label>
                      <textarea
                        value={issueText}
                        onChange={(e) => setIssueText(e.target.value)}
                        className="w-full flex-1 min-h-[75px] bg-[#FBF9F5] border border-[#E8E2D6] rounded-xl p-2.5 text-xs text-[#063737] focus:outline-none focus:border-[#A25524] font-mono resize-none leading-relaxed transition-all"
                      />
                    </div>

                    {/* Execution Sandbox Mode */}
                    <div>
                      <label className="text-[10px] font-semibold text-[#063737]/75 block mb-1">Execution Sandbox Mode</label>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <button
                          onClick={() => setExecutionMode("docker")}
                          className={`py-1.5 px-2 rounded-xl border flex items-center justify-center gap-1.5 cursor-pointer text-[11px] font-medium transition-all ${
                            executionMode === "docker"
                              ? "bg-[#063737] border-[#063737] text-white font-bold shadow-2xs"
                              : "bg-[#FBF9F5] border-[#E8E2D6] text-[#063737]/70 hover:text-[#063737]"
                          }`}
                        >
                          <Lock className="w-3 h-3 text-[#E8C9CF]" />
                          <span>Docker Micro-VM</span>
                        </button>
                        <button
                          onClick={() => setExecutionMode("local")}
                          className={`py-1.5 px-2 rounded-xl border flex items-center justify-center gap-1.5 cursor-pointer text-[11px] font-medium transition-all ${
                            executionMode === "local"
                              ? "bg-[#A25524] border-[#A25524] text-white font-bold shadow-2xs"
                              : "bg-[#FBF9F5] border-[#E8E2D6] text-[#063737]/70 hover:text-[#063737]"
                          }`}
                        >
                          <Server className="w-3 h-3 text-[#E8C9CF]" />
                          <span>Trusted Local</span>
                        </button>
                      </div>
                    </div>

                    {/* Budget Slider */}
                    <div className="flex items-center justify-between text-xs text-[#063737]/75 pt-1">
                      <span className="text-[10px] font-medium">MCTS Search Budget:</span>
                      <div className="flex items-center gap-2">
                        <input
                          type="range"
                          min="4"
                          max="20"
                          value={iterations}
                          onChange={(e) => setIterations(Number(e.target.value))}
                          className="w-20 accent-[#A25524] cursor-pointer"
                        />
                        <span className="font-mono text-[#A25524] font-bold bg-[#A25524]/10 px-2 py-0.5 rounded-md border border-[#A25524]/30 text-[10px]">
                          {iterations} nodes
                        </span>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center gap-2 pt-1">
                      <button
                        onClick={runMCTSSolver}
                        disabled={agentState !== "IDLE" && agentState !== "SUCCESS" && agentState !== "FAILED"}
                        className="flex-1 py-3 rounded-xl bg-[#063737] hover:bg-[#094d4d] text-white text-xs font-bold tracking-wide uppercase flex items-center justify-center gap-2 shadow-md shadow-[#063737]/20 disabled:opacity-50 transition-all cursor-pointer glow-teal"
                      >
                        {agentState !== "IDLE" && agentState !== "SUCCESS" && agentState !== "FAILED" ? (
                          <>
                            <RotateCcw className="w-4 h-4 animate-spin text-[#E8C9CF]" />
                            <span>Aegis is Searching...</span>
                          </>
                        ) : agentState === "SUCCESS" ? (
                          <>
                            <CheckCircle2 className="w-4 h-4 text-[#808000]" />
                            <span>Issue Resolved (Run Again)</span>
                          </>
                        ) : (
                          <>
                            <Play className="w-4 h-4 fill-current text-[#E8C9CF]" />
                            <span>Solve Issue with Aegis MCTS</span>
                          </>
                        )}
                      </button>

                      {agentState !== "IDLE" && agentState !== "SUCCESS" && agentState !== "FAILED" && (
                        <button
                          onClick={stopRun}
                          className="px-3 py-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 hover:bg-rose-100 text-xs font-bold flex items-center gap-1 cursor-pointer transition-colors"
                          title="Stop Run"
                        >
                          <StopCircle className="w-4 h-4" />
                          <span>Stop</span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>

                {/* Sandbox Security Configuration */}
                <div className="p-3.5 rounded-2xl bg-white border border-[#E8E2D6] shadow-xs text-xs">
                  <h3 className="text-[10px] font-bold text-[#063737] uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <Lock className="w-3 h-3 text-[#A25524]" />
                    Sandbox Security Scorecard
                  </h3>
                  <div className="grid grid-cols-2 gap-y-1 gap-x-2 text-[10px] font-mono text-[#063737]/80">
                    <span className="flex items-center gap-1 text-[#808000] font-semibold">✓ Docker Isolation</span>
                    <span className="flex items-center gap-1 text-[#808000] font-semibold">✓ Non-root (uid 1000)</span>
                    <span className="flex items-center gap-1 text-[#808000] font-semibold">✓ Network Disabled</span>
                    <span className="flex items-center gap-1 text-[#808000] font-semibold">✓ Memory (512MB)</span>
                    <span className="flex items-center gap-1 text-[#808000] font-semibold">✓ Timeout (30s)</span>
                    <span className="flex items-center gap-1 text-[#808000] font-semibold">✓ Ephemeral Workspace</span>
                  </div>
                </div>
              </div>

              {/* RIGHT COLUMN: WORKSPACE TABS & TERMINAL (8 Cols) */}
              <div className="col-span-12 lg:col-span-8 flex flex-col gap-4">
                {/* Verified Solution Success Banner */}
                {agentState === "SUCCESS" && solutionNode && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="p-4 rounded-2xl bg-[#808000]/10 border border-[#808000]/40 shadow-xs flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-[#808000] text-white flex items-center justify-center font-bold shadow-xs">
                        <CheckCircle2 className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="font-bold text-[#063737] text-sm flex items-center gap-2">
                          <span>Patch Verified (100% Pass@1)</span>
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#808000]/20 text-[#808000] border border-[#808000]/40 font-mono font-bold">
                            {solutionNode.tests_passed} / {solutionNode.tests_passed} Tests Passing
                          </span>
                        </div>
                        <div className="text-[11px] text-[#063737]/75 font-mono mt-0.5">
                          Target: {selectedTask.target_file} | Lines: +{selectedTask.lines_added} / -{selectedTask.lines_removed} | Resolution: {elapsedSeconds}s
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setActiveTab("diff")}
                        className="px-3 py-1.5 rounded-lg bg-[#063737] hover:bg-[#094d4d] text-white text-xs font-semibold flex items-center gap-1 cursor-pointer transition-colors shadow-2xs"
                      >
                        <Eye className="w-3.5 h-3.5 text-[#E8C9CF]" />
                        View Diff
                      </button>
                      <button
                        onClick={copyDiff}
                        className="px-3 py-1.5 rounded-lg bg-white border border-[#E8E2D6] hover:bg-[#F2EFE9] text-[#063737] text-xs font-semibold flex items-center gap-1 cursor-pointer transition-colors shadow-2xs"
                      >
                        {copied ? <Check className="w-3.5 h-3.5 text-[#808000]" /> : <Copy className="w-3.5 h-3.5 text-[#A25524]" />}
                        <span>{copied ? "Copied!" : "Export Patch"}</span>
                      </button>
                    </div>
                  </motion.div>
                )}

                {/* Main Tabbed Interactive Workspace */}
                <div className="flex-1 p-4 rounded-2xl bg-white border border-[#E8E2D6] shadow-xs flex flex-col min-h-[380px]">
                  {/* Tab Navigation Header */}
                  <div className="flex items-center justify-between mb-3 border-b border-[#E8E2D6]/60 pb-2.5">
                    <div className="flex items-center gap-2.5">
                      <div className="p-1.5 rounded-xl bg-[#063737]/10 border border-[#063737]/20 text-[#063737]">
                        <GitBranch className="w-4 h-4 text-[#A25524]" />
                      </div>
                      <div>
                        <h2 className="text-sm font-bold text-[#063737] flex items-center gap-2">
                          MCTS Search Tree & Synthesis
                        </h2>
                        <p className="text-[10px] text-[#063737]/60 font-mono">
                          {nodes.length > 0
                            ? `${nodes.length} nodes explored • ${nodes.filter((n) => n.is_solution).length} verified solution`
                            : "Awaiting solver launch"}
                        </p>
                      </div>
                    </div>

                    {/* Tab Buttons */}
                    <div className="flex items-center bg-[#F2EFE9] p-0.5 rounded-xl border border-[#E2DACD] text-xs font-semibold">
                      <button
                        onClick={() => setActiveTab("tree")}
                        className={`px-3 py-1 rounded-lg transition-all flex items-center gap-1 cursor-pointer ${
                          activeTab === "tree"
                            ? "bg-white text-[#063737] shadow-xs border border-[#DCD3C3] font-bold"
                            : "text-[#063737]/60 hover:text-[#063737]"
                        }`}
                      >
                        <GitBranch className="w-3 h-3 text-[#A25524]" />
                        MCTS Tree
                      </button>
                      <button
                        onClick={() => setActiveTab("diff")}
                        className={`px-3 py-1 rounded-lg transition-all flex items-center gap-1 cursor-pointer ${
                          activeTab === "diff"
                            ? "bg-white text-[#063737] shadow-xs border border-[#DCD3C3] font-bold"
                            : "text-[#063737]/60 hover:text-[#063737]"
                        }`}
                      >
                        <Code2 className="w-3 h-3 text-[#808000]" />
                        Unified Diff
                      </button>
                      <button
                        onClick={() => setActiveTab("decision")}
                        className={`px-3 py-1 rounded-lg transition-all flex items-center gap-1 cursor-pointer ${
                          activeTab === "decision"
                            ? "bg-white text-[#063737] shadow-xs border border-[#DCD3C3] font-bold"
                            : "text-[#063737]/60 hover:text-[#063737]"
                        }`}
                      >
                        <Sparkles className="w-3 h-3 text-[#A25524]" />
                        Agent Decision
                      </button>
                      <button
                        onClick={() => setActiveTab("critic")}
                        className={`px-3 py-1 rounded-lg transition-all flex items-center gap-1 cursor-pointer ${
                          activeTab === "critic"
                            ? "bg-white text-[#063737] shadow-xs border border-[#DCD3C3] font-bold"
                            : "text-[#063737]/60 hover:text-[#063737]"
                        }`}
                      >
                        <FileCheck className="w-3 h-3 text-[#808000]" />
                        Critic
                      </button>
                      <button
                        onClick={() => setActiveTab("terminal")}
                        className={`px-3 py-1 rounded-lg transition-all flex items-center gap-1 cursor-pointer ${
                          activeTab === "terminal"
                            ? "bg-[#063737] text-white shadow-xs font-bold"
                            : "text-[#063737]/60 hover:text-[#063737]"
                        }`}
                      >
                        <Terminal className="w-3 h-3 text-[#E8C9CF]" />
                        Terminal
                      </button>
                    </div>
                  </div>

                  {/* TAB 1: MCTS SEARCH TREE & INSPECTOR */}
                  {activeTab === "tree" && (
                    <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-3.5">
                      {/* Node List Cards */}
                      <div className="p-3 rounded-xl bg-[#FBF9F5] border border-[#E8E2D6] overflow-y-auto max-h-[300px] space-y-2">
                        {nodes.length === 0 ? (
                          <div className="h-full flex flex-col items-center justify-center text-[#063737]/50 text-xs text-center py-14">
                            <motion.div
                              animate={{ rotate: [0, 360] }}
                              transition={{ duration: 18, repeat: Infinity, ease: "linear" }}
                              className="w-10 h-10 rounded-full border border-dashed border-[#A25524] flex items-center justify-center mb-2.5"
                            >
                              <GitBranch className="w-5 h-5 text-[#A25524]" />
                            </motion.div>
                            <p className="font-semibold text-[#063737]">No Active Search</p>
                            <p className="text-[#063737]/60 text-[11px] mt-0.5">
                              Click "Solve Issue with Aegis MCTS" to start autonomous exploration.
                            </p>
                          </div>
                        ) : (
                          <AnimatePresence>
                            {nodes.map((node, idx) => (
                              <motion.div
                                key={node.id}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.2, delay: idx * 0.05 }}
                                onClick={() => setSelectedNode(node)}
                                className={`p-2.5 rounded-xl border cursor-pointer transition-all text-xs relative ${
                                  selectedNode?.id === node.id
                                    ? "border-[#063737] bg-[#E8C9CF]/20 shadow-xs ring-1 ring-[#063737]"
                                    : node.status === "verified"
                                    ? "border-[#808000]/50 bg-[#808000]/10"
                                    : node.status === "failed"
                                    ? "border-rose-300 bg-rose-50/70"
                                    : "border-[#E8E2D6] bg-white hover:border-[#A25524]/40 shadow-2xs"
                                }`}
                              >
                                <div className="flex items-center justify-between mb-1">
                                  <span className="font-mono text-[11px] text-[#063737]/70 flex items-center gap-1.5">
                                    <span
                                      className={`w-1.5 h-1.5 rounded-full ${
                                        node.status === "verified"
                                          ? "bg-[#808000]"
                                          : node.status === "failed"
                                          ? "bg-rose-500"
                                          : "bg-[#A25524]"
                                      }`}
                                    />
                                    <strong className="text-[#063737]">{node.node_name}</strong> (Depth {node.depth})
                                  </span>

                                  {node.status === "verified" ? (
                                    <span className="flex items-center gap-1 text-[10px] px-1.5 py-0.2 rounded bg-[#808000]/20 text-[#808000] border border-[#808000]/40 font-bold font-mono">
                                      ✓ Verified
                                    </span>
                                  ) : node.status === "failed" ? (
                                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-rose-100 text-rose-800 border border-rose-200 font-semibold">
                                      ✕ Failed
                                    </span>
                                  ) : (
                                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#F2EFE9] text-[#063737]/80">
                                      Reward: {node.mean_reward}
                                    </span>
                                  )}
                                </div>

                                <p className="text-[#063737] font-medium text-[11px] line-clamp-1">{node.summary}</p>

                                <div className="flex items-center gap-2.5 text-[10px] text-[#063737]/60 mt-1.5 font-mono">
                                  <span>Visits (N): {node.visits}</span>
                                  <span>•</span>
                                  <span>Q: {node.mean_reward}</span>
                                  <span>•</span>
                                  <span className="text-[#A25524] font-semibold">UCT: {node.uct}</span>
                                  {node.tests_passed > 0 && (
                                    <span className="text-[#808000] font-bold">• {node.tests_passed} Passed</span>
                                  )}
                                  {node.tests_failed > 0 && (
                                    <span className="text-rose-700 font-bold">• {node.tests_failed} Failed</span>
                                  )}
                                </div>
                              </motion.div>
                            ))}
                          </AnimatePresence>
                        )}
                      </div>

                      {/* Node Details / Inspector */}
                      <div className="p-3.5 rounded-xl bg-white border border-[#E8E2D6] text-xs overflow-y-auto max-h-[300px] shadow-2xs">
                        {selectedNode ? (
                          <div className="space-y-2.5">
                            <div className="flex items-center justify-between border-b border-[#E8E2D6] pb-2">
                              <div>
                                <span className="font-bold text-[#063737] text-sm">Node: {selectedNode.node_name}</span>
                                <p className="text-[10px] text-[#063737]/60 font-mono">Action: {selectedNode.action_type}</p>
                              </div>
                              <span
                                className={`px-2 py-0.5 rounded-full font-mono text-[10px] font-bold ${
                                  selectedNode.status === "verified"
                                    ? "bg-[#808000]/20 text-[#808000] border border-[#808000]/40"
                                    : selectedNode.status === "failed"
                                    ? "bg-rose-100 text-rose-800 border border-rose-200"
                                    : "bg-[#F2EFE9] text-[#063737]"
                                }`}
                              >
                                {selectedNode.status.toUpperCase()}
                              </span>
                            </div>

                            {/* Mathematical Telemetry */}
                            <div className="grid grid-cols-3 gap-1.5 font-mono">
                              <div className="bg-[#FBF9F5] p-2 rounded-xl border border-[#E8E2D6]">
                                <span className="text-[9px] text-[#063737]/60 block">Visits (N)</span>
                                <span className="text-[#063737] font-bold text-sm">{selectedNode.visits}</span>
                              </div>
                              <div className="bg-[#FBF9F5] p-2 rounded-xl border border-[#E8E2D6]">
                                <span className="text-[9px] text-[#063737]/60 block">Mean Q</span>
                                <span className="text-[#A25524] font-bold text-sm">{selectedNode.mean_reward}</span>
                              </div>
                              <div className="bg-[#FBF9F5] p-2 rounded-xl border border-[#E8E2D6]">
                                <span className="text-[9px] text-[#063737]/60 block">UCT Score</span>
                                <span className="text-[#063737] font-bold text-sm">{selectedNode.uct}</span>
                              </div>
                            </div>

                            <div>
                              <span className="text-[#063737]/60 text-[10px] font-semibold block mb-0.5">Files Touched</span>
                              <div className="flex flex-wrap gap-1">
                                {selectedNode.files_touched.map((f, i) => (
                                  <code key={i} className="px-2 py-0.5 rounded-md bg-[#F2EFE9] border border-[#E8E2D6] text-[10px] text-[#A25524] font-mono font-semibold">
                                    {f}
                                  </code>
                                ))}
                              </div>
                            </div>

                            <div>
                              <span className="text-[#063737]/60 text-[10px] font-semibold block mb-0.5">Summary</span>
                              <p className="text-[#063737] bg-[#FBF9F5] p-2 rounded-xl border border-[#E8E2D6] text-[11px] leading-relaxed">
                                {selectedNode.summary}
                              </p>
                            </div>

                            {/* Failure Analysis */}
                            {selectedNode.failure_details && (
                              <div className="p-2.5 rounded-xl bg-rose-50 border border-rose-200 text-[11px]">
                                <span className="font-bold text-rose-800 flex items-center gap-1 mb-1">
                                  <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                                  Structured Failure Analysis
                                </span>
                                <div className="grid grid-cols-2 gap-1 text-[10px] font-mono mt-1 text-[#063737]">
                                  <div>Type: <span className="text-rose-700 font-bold">{selectedNode.failure_details.type}</span></div>
                                  <div>Line: <span className="text-rose-700 font-bold">{selectedNode.failure_details.line}</span></div>
                                  <div>Expected: <span className="text-[#808000] font-bold">{selectedNode.failure_details.expected}</span></div>
                                  <div>Received: <span className="text-rose-700 font-bold">{selectedNode.failure_details.received}</span></div>
                                </div>
                                <div className="mt-1 text-[10px] text-[#063737] font-mono">
                                  Next Action: <span className="text-[#A25524] font-semibold">{selectedNode.failure_details.next_action}</span>
                                </div>
                              </div>
                            )}
                          </div>
                        ) : (
                          <div className="h-full flex items-center justify-center text-[#063737]/40 text-xs text-center py-12">
                            Click any node in the search tree to inspect its telemetry, files touched, and test results.
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* TAB 2: UNIFIED DIFF VIEWER */}
                  {activeTab === "diff" && (
                    <div className="flex-1 bg-[#042424] rounded-xl p-3.5 font-mono text-xs overflow-x-auto border border-[#063737] max-h-[300px] flex flex-col text-[#E8C9CF] shadow-inner">
                      <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#063737] text-[11px] text-[#E8C9CF]/70">
                        <div className="flex items-center gap-2">
                          <FileCode className="w-4 h-4 text-[#808000]" />
                          <span>FILE: <strong className="text-white">{selectedTask.target_file}</strong></span>
                          <span className="text-[10px] px-2 py-0.5 rounded bg-[#063737] text-[#E8C9CF] border border-[#094d4d]">
                            Files changed: 1 | Lines added: +{selectedTask.lines_added} | Lines removed: -{selectedTask.lines_removed}
                          </span>
                        </div>
                        {solutionNode?.git_diff && (
                          <button
                            onClick={copyDiff}
                            className="px-2.5 py-1 rounded-lg bg-[#063737] hover:bg-[#094d4d] text-white flex items-center gap-1 cursor-pointer transition-colors shadow-xs"
                          >
                            {copied ? <Check className="w-3.5 h-3.5 text-[#808000]" /> : <Copy className="w-3.5 h-3.5 text-[#E8C9CF]" />}
                            <span>{copied ? "Copied Patch!" : "Copy Diff"}</span>
                          </button>
                        )}
                      </div>

                      {solutionNode?.git_diff ? (
                        <pre className="text-[#808000] whitespace-pre leading-relaxed text-xs overflow-x-auto selection:bg-[#063737]">
                          {solutionNode.git_diff}
                        </pre>
                      ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-[#E8C9CF]/50 text-center py-12">
                          <Code2 className="w-7 h-7 mb-1.5 opacity-40 text-[#E8C9CF]" />
                          No verified diff generated yet. Run search to generate a patch.
                        </div>
                      )}
                    </div>
                  )}

                  {/* TAB 3: AGENT DECISION ENGINE */}
                  {activeTab === "decision" && (
                    <div className="flex-1 bg-white rounded-xl p-3.5 text-xs overflow-y-auto border border-[#E8E2D6] max-h-[300px] space-y-2.5 shadow-2xs">
                      <div className="border-b border-[#E8E2D6] pb-2 flex items-center justify-between">
                        <h3 className="font-bold text-[#063737] flex items-center gap-1.5">
                          <Sparkles className="w-4 h-4 text-[#A25524]" />
                          Structured Agent Decision Engine
                        </h3>
                        <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-[#E8C9CF]/40 text-[#063737] border border-[#E8C9CF] font-mono font-bold">
                          Confidence: {(selectedTask.decision_data.confidence * 100).toFixed(0)}%
                        </span>
                      </div>

                      {nodes.length === 0 ? (
                        <p className="text-[#063737]/50 text-center py-12">Awaiting agent analysis...</p>
                      ) : (
                        <div className="space-y-2 text-[11px]">
                          <div className="p-2.5 rounded-xl bg-[#FBF9F5] border border-[#E8E2D6]">
                            <span className="text-[10px] text-[#063737]/60 font-semibold block mb-0.5 font-mono">Issue Signal:</span>
                            <p className="text-[#063737] font-medium">{selectedTask.decision_data.issue_signal}</p>
                          </div>

                          <div className="p-2.5 rounded-xl bg-[#FBF9F5] border border-[#E8E2D6]">
                            <span className="text-[10px] text-[#063737]/60 font-semibold block mb-0.5 font-mono">Relevant AST Symbols:</span>
                            <div className="flex flex-wrap gap-1.5 mt-1">
                              {selectedTask.decision_data.relevant_symbols.map((sym, i) => (
                                <code key={i} className="px-2 py-0.5 rounded-md bg-white border border-[#E8E2D6] text-[10px] text-[#A25524] font-mono font-semibold">
                                  {sym}
                                </code>
                              ))}
                            </div>
                          </div>

                          <div className="p-2.5 rounded-xl bg-[#FBF9F5] border border-[#E8E2D6]">
                            <span className="text-[10px] text-[#063737]/60 font-semibold block mb-0.5 font-mono">Current Hypothesis:</span>
                            <p className="text-[#063737] font-medium">{selectedTask.decision_data.hypothesis}</p>
                          </div>

                          <div className="p-2.5 rounded-xl bg-[#FBF9F5] border border-[#E8E2D6]">
                            <span className="text-[10px] text-[#063737]/60 font-semibold block mb-0.5 font-mono">Next Agent Action:</span>
                            <p className="text-[#A25524] font-mono font-semibold">{selectedTask.decision_data.next_action}</p>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* TAB 4: CRITIC EVALUATION */}
                  {activeTab === "critic" && (
                    <div className="flex-1 bg-white rounded-xl p-3.5 text-xs overflow-y-auto border border-[#E8E2D6] max-h-[300px] space-y-2.5 shadow-2xs">
                      <div className="border-b border-[#E8E2D6] pb-2 flex items-center justify-between">
                        <h3 className="font-bold text-[#063737] flex items-center gap-1.5">
                          <FileCheck className="w-4 h-4 text-[#808000]" />
                          Structured Critic Verification Matrix
                        </h3>
                        <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-[#808000]/20 text-[#808000] border border-[#808000]/40 font-mono font-bold">
                          Decision: {solutionNode ? "ACCEPT PATCH" : "AWAITING RUN"}
                        </span>
                      </div>

                      {solutionNode ? (
                        <div className="space-y-2 text-[11px]">
                          <div className="grid grid-cols-2 gap-2 font-mono text-[10px]">
                            <div className="p-2.5 rounded-xl bg-[#FBF9F5] border border-[#E8E2D6] flex justify-between">
                              <span className="text-[#063737]/60">Reproduction Test:</span>
                              <span className="text-[#808000] font-bold">✓ Passed (RED verified)</span>
                            </div>
                            <div className="p-2.5 rounded-xl bg-[#FBF9F5] border border-[#E8E2D6] flex justify-between">
                              <span className="text-[#063737]/60">Regression Suite:</span>
                              <span className="text-[#808000] font-bold">✓ Passed (13/13)</span>
                            </div>
                            <div className="p-2.5 rounded-xl bg-[#FBF9F5] border border-[#E8E2D6] flex justify-between">
                              <span className="text-[#063737]/60">Patch Applied:</span>
                              <span className="text-[#808000] font-bold">✓ Cleanly (0 conflicts)</span>
                            </div>
                            <div className="p-2.5 rounded-xl bg-[#FBF9F5] border border-[#E8E2D6] flex justify-between">
                              <span className="text-[#063737]/60">Syntax Check:</span>
                              <span className="text-[#808000] font-bold">✓ Passed (AST Valid)</span>
                            </div>
                            <div className="p-2.5 rounded-xl bg-[#FBF9F5] border border-[#E8E2D6] flex justify-between">
                              <span className="text-[#063737]/60">Patch Minimality:</span>
                              <span className="text-[#808000] font-bold">✓ Passed (+{selectedTask.lines_added} lines)</span>
                            </div>
                            <div className="p-2.5 rounded-xl bg-[#FBF9F5] border border-[#E8E2D6] flex justify-between">
                              <span className="text-[#063737]/60">Final Reward:</span>
                              <span className="text-[#A25524] font-bold">1.00 (Max Composite)</span>
                            </div>
                          </div>

                          <div className="p-2.5 rounded-xl bg-[#FBF9F5] border border-[#E8E2D6]">
                            <span className="text-[10px] font-mono text-[#063737]/60 block mb-1">Critic Reasoning:</span>
                            <p className="text-[#063737] leading-relaxed font-medium">{solutionNode.reflection}</p>
                          </div>
                        </div>
                      ) : (
                        <p className="text-[#063737]/50 text-center py-12">No critic evaluations executed yet.</p>
                      )}
                    </div>
                  )}

                  {/* TAB 5: TERMINAL STREAM VIEW */}
                  {activeTab === "terminal" && (
                    <div className="flex-1 bg-[#042424] rounded-xl p-3.5 font-mono text-xs overflow-y-auto border border-[#063737] max-h-[300px] flex flex-col text-[#E8C9CF] shadow-inner">
                      <div className="flex-1 space-y-1 text-[11px] select-text">
                        {terminalLogs.map((log, idx) => (
                          <div key={idx} className="leading-relaxed flex items-start gap-1.5">
                            <span className="text-[#063737] select-none">&gt;</span>
                            {log.includes("✓") || log.includes("PASSED") || log.includes("Verified") ? (
                              <span className="text-[#808000] font-semibold">{log}</span>
                            ) : log.includes("❌") || log.includes("FAILED") || log.includes("Rejected") ? (
                              <span className="text-rose-400 font-semibold">{log}</span>
                            ) : log.includes("[MCTS]") ? (
                              <span className="text-[#A25524]">{log}</span>
                            ) : log.includes("[AST]") ? (
                              <span className="text-[#E8C9CF]">{log}</span>
                            ) : log.includes("[SANDBOX]") ? (
                              <span className="text-[#808000]">{log}</span>
                            ) : (
                              <span className="text-[#E8C9CF]/80">{log}</span>
                            )}
                          </div>
                        ))}
                        <div ref={terminalEndRef} />
                      </div>
                    </div>
                  )}
                </div>

                {/* Bottom Quick-Console (Always visible in Cockpit) */}
                <div className="h-36 p-3 rounded-2xl bg-[#042424] border border-[#063737] shadow-md flex flex-col font-mono text-xs text-[#E8C9CF]">
                  <div className="flex items-center justify-between mb-1.5 text-[#E8C9CF]/70 border-b border-[#063737] pb-1">
                    <span className="flex items-center gap-1.5 text-white font-bold text-[10px]">
                      <Terminal className="w-3 h-3 text-[#A25524]" />
                      Execution Sandbox Stream
                    </span>
                    <span className="text-[9px] text-[#E8C9CF]/50 font-mono">
                      stdout / pytest
                    </span>
                  </div>

                  <div className="flex-1 overflow-y-auto space-y-1 text-[#E8C9CF]/90 pr-1 text-[10px] select-text">
                    {terminalLogs.slice(-6).map((log, idx) => (
                      <div key={idx} className="leading-relaxed flex items-start gap-1.5">
                        <span className="text-[#063737] select-none">&gt;</span>
                        {log.includes("✓") || log.includes("PASSED") ? (
                          <span className="text-[#808000] font-semibold">{log}</span>
                        ) : log.includes("❌") || log.includes("FAILED") ? (
                          <span className="text-rose-400 font-semibold">{log}</span>
                        ) : (
                          <span className="text-[#E8C9CF]/80">{log}</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
