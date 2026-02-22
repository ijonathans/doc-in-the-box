import type { KeyboardEvent } from "react";
import { useEffect, useRef, useState } from "react";
import {
  ArrowUpRight,
  CalendarCheck,
  History,
  MessageCircle,
  ShieldCheck,
  User
} from "lucide-react";

import { AppointmentView } from "@/components/AppointmentView";
import { HistoryChatView } from "@/components/HistoryChatView";
import { InsuranceView } from "@/components/InsuranceView";
import { ParticleSphere } from "@/components/ParticleSphere";
import { PrimaryActionButton } from "@/components/PrimaryActionButton";
import { ProfileView } from "@/components/ProfileView";
import { SidebarNavItem } from "@/components/SidebarNavItem";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import {
  API_BASE,
  consumeCallSummary,
  getPendingCallSummary,
  sendChatMessage
} from "@/api";

type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

export default function App() {
  const [activeNav, setActiveNav] = useState("chat");
  const [prompt, setPrompt] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatSessionId, setChatSessionId] = useState<string | null>(null);
  const [isSending, setIsSending] = useState(false);
  const callSummaryPollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const callSummaryEventSourceRef = useRef<EventSource | null>(null);
  const callSummaryShownRef = useRef(false);

  const navItemsMain = [
    { id: "chat", label: "Chat", icon: MessageCircle },
    { id: "appointment", label: "Appointment", icon: CalendarCheck },
    { id: "insurance", label: "Insurance", icon: ShieldCheck },
    { id: "profile", label: "Profile", icon: User },
  ];
  const navItemHistory = { id: "history", label: "History Chat", icon: History };
  const navItems = [...navItemsMain, navItemHistory];

  const isChatMode = messages.length > 0;

  async function handleSubmit() {
    const nextPrompt = prompt.trim();
    if (!nextPrompt || isSending) return;

    setPrompt("");
    setMessages((previous) => [
      ...previous,
      { id: `${Date.now()}-user`, role: "user", content: nextPrompt }
    ]);

    setIsSending(true);
    try {
      const response = await sendChatMessage(nextPrompt, chatSessionId);
      setChatSessionId(response.session_id);
      setMessages((previous) => [
        ...previous,
        { id: `${Date.now()}-assistant`, role: "assistant", content: response.reply }
      ]);
      if (response.outbound_call_started && response.session_id) {
        const sessionId = response.session_id;
        callSummaryShownRef.current = false;
        if (callSummaryPollRef.current) clearInterval(callSummaryPollRef.current);
        if (callSummaryEventSourceRef.current) {
          callSummaryEventSourceRef.current.close();
          callSummaryEventSourceRef.current = null;
        }

        const stopPollingAndSSE = () => {
          if (callSummaryPollRef.current) {
            clearInterval(callSummaryPollRef.current);
            callSummaryPollRef.current = null;
          }
          if (callSummaryEventSourceRef.current) {
            callSummaryEventSourceRef.current.close();
            callSummaryEventSourceRef.current = null;
          }
        };

        const showSummaryInChat = (summary: string) => {
          if (callSummaryShownRef.current) return;
          callSummaryShownRef.current = true;
          stopPollingAndSSE();
          const reply = "**Call summary**\n\n" + summary.trim();
          setMessages((prev) => [
            ...prev,
            { id: `${Date.now()}-call-summary`, role: "assistant", content: reply }
          ]);
          void consumeCallSummary(sessionId);
        };

        const eventsUrl = `${API_BASE}/chat/events?session_id=${encodeURIComponent(sessionId)}`;
        const es = new EventSource(eventsUrl);
        callSummaryEventSourceRef.current = es;
        es.addEventListener("call_summary_ready", async () => {
          try {
            const { summary } = await getPendingCallSummary(sessionId);
            if (summary?.trim()) showSummaryInChat(summary);
          } catch {
            // fallback to poll
          }
        });
        es.onerror = () => {
          es.close();
          callSummaryEventSourceRef.current = null;
        };

        const startedAt = Date.now();
        const POLL_MS = 5000;
        const MAX_POLL_MS = 10 * 60 * 1000;
        const GIVE_UP_MS = 10 * 60 * 1000;
        callSummaryPollRef.current = setInterval(async () => {
          const elapsed = Date.now() - startedAt;
          if (elapsed > MAX_POLL_MS || elapsed > GIVE_UP_MS) {
            stopPollingAndSSE();
            return;
          }
          try {
            const { summary } = await getPendingCallSummary(sessionId);
            if (summary?.trim()) showSummaryInChat(summary);
          } catch {
            // ignore poll errors
          }
        }, POLL_MS);
      }
    } catch {
      setMessages((previous) => [
        ...previous,
        {
          id: `${Date.now()}-assistant-error`,
          role: "assistant",
          content: "I could not generate a response right now. Please check the backend server and try again."
        }
      ]);
    } finally {
      setIsSending(false);
    }
  }

  function handlePromptKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void handleSubmit();
    }
  }

  useEffect(() => {
    return () => {
      if (callSummaryPollRef.current) clearInterval(callSummaryPollRef.current);
      if (callSummaryEventSourceRef.current) {
        callSummaryEventSourceRef.current.close();
        callSummaryEventSourceRef.current = null;
      }
    };
  }, []);

  return (
    <main className="min-h-screen">
      <aside className="fixed bottom-0 left-0 top-0 hidden w-[72px] flex-col items-center justify-between bg-sidebar py-5 md:flex">
        <div className="flex flex-col items-center gap-6">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-violet-500 via-fuchsia-500 to-blue-500 shadow-md" />
          <nav className="flex flex-col items-center gap-3">
            {navItemsMain.map((item) => (
              <SidebarNavItem
                key={item.id}
                icon={item.icon}
                label={item.label}
                active={activeNav === item.id}
                onClick={() => setActiveNav(item.id)}
              />
            ))}
            <div className="mt-2 border-t border-white/10 pt-2">
              <SidebarNavItem
                key={navItemHistory.id}
                icon={navItemHistory.icon}
                label={navItemHistory.label}
                active={activeNav === navItemHistory.id}
                onClick={() => setActiveNav(navItemHistory.id)}
              />
            </div>
          </nav>
        </div>
        <div className="flex flex-col items-center gap-2">
          <Avatar className="h-10 w-10 border border-white/25">
            <AvatarImage
              src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=120&q=80"
              alt="User avatar"
            />
            <AvatarFallback>AI</AvatarFallback>
          </Avatar>
          <Badge className="border-none text-[10px]">PRO</Badge>
        </div>
      </aside>

      <div className="sticky top-0 z-20 flex h-14 flex-shrink-0 items-center border-b border-white/10 bg-sidebar md:hidden pl-[max(1rem,env(safe-area-inset-left))] pr-[max(1rem,env(safe-area-inset-right))]">
        <div className="mx-auto flex max-w-content flex-wrap items-center justify-center gap-2">
          {navItems.map((item) => (
            <SidebarNavItem
              key={item.id}
              icon={item.icon}
              label={item.label}
              active={activeNav === item.id}
              onClick={() => setActiveNav(item.id)}
            />
          ))}
        </div>
      </div>

      <section className="relative py-8 pl-[max(1rem,env(safe-area-inset-left))] pr-[max(1rem,env(safe-area-inset-right))] md:ml-[72px] md:px-8 md:py-10">
        <div className="mx-auto flex w-full max-w-content flex-col gap-16">
          {activeNav === "appointment" && <AppointmentView />}
          {activeNav === "insurance" && <InsuranceView />}
          {activeNav === "profile" && <ProfileView />}
          {activeNav === "history" && <HistoryChatView />}
          {activeNav === "chat" && !isChatMode ? (
            <>
              <div className="flex min-h-[calc(100vh-3.5rem)] flex-col items-center justify-center gap-8 text-center md:min-h-[calc(100vh-4rem)]">
                <ParticleSphere />
                <h1 className="max-w-xl text-balance text-2xl font-semibold md:text-3xl">
                  How can we help you today?
                </h1>

                <Card className="w-full max-w-3xl rounded-2xl border border-border shadow-input">
                  <CardContent className="space-y-4 p-6">
                    <Textarea
                      value={prompt}
                      onChange={(event) => setPrompt(event.target.value)}
                      onKeyDown={handlePromptKeyDown}
                      placeholder="Describe your symptoms or health concern..."
                      className="min-h-[88px] text-base"
                    />
                    <div className="flex justify-end">
                      <PrimaryActionButton
                        type="button"
                        iconOnly
                        onClick={handleSubmit}
                        disabled={isSending || !prompt.trim()}
                        aria-label="Send prompt"
                      />
                    </div>
                  </CardContent>
                </Card>
              </div>
            </>
          ) : activeNav === "chat" ? (
            <section className="fixed bottom-0 left-0 right-0 top-14 flex min-h-0 flex-col bg-background md:left-[72px] md:top-0">
              <div className="min-h-0 flex-1 overflow-y-auto px-4 pb-6 pt-4 md:px-8 md:pt-8">
                <div className="mx-auto flex min-h-full w-full max-w-5xl flex-col justify-end rounded-2xl border border-border bg-card p-4 shadow-card md:p-6">
                  <div className="space-y-4">
                    {messages.map((message) => (
                      <div key={message.id} className={message.role === "user" ? "flex justify-end" : "flex justify-start"}>
                        <div
                          className={
                            message.role === "user"
                              ? "max-w-[82%] rounded-2xl rounded-br-md bg-primary px-4 py-3 text-sm text-white"
                              : "max-w-[82%] rounded-2xl rounded-bl-md bg-[#EEE8DC] px-4 py-3 text-sm text-foreground"
                          }
                        >
                          {message.content}
                        </div>
                      </div>
                    ))}
                    {isSending ? (
                      <div className="flex justify-start">
                        <div className="rounded-2xl rounded-bl-md bg-[#EEE8DC] px-4 py-3 text-sm text-muted-foreground">
                          Thinking...
                        </div>
                      </div>
                    ) : null}
                  </div>
                </div>
              </div>

              <div className="border-t border-border bg-background px-4 py-4 pb-[max(1rem,env(safe-area-inset-bottom))] md:px-8">
                <div className="mx-auto w-full max-w-5xl">
                  <Card className="w-full rounded-2xl border border-border shadow-input">
                    <CardContent className="space-y-4 p-4 md:p-5">
                      <Textarea
                        value={prompt}
                        onChange={(event) => setPrompt(event.target.value)}
                        onKeyDown={handlePromptKeyDown}
                        placeholder="Type a follow-up and press Enter to send..."
                        rows={1}
                        className="!min-h-[1.5rem] py-0 text-base"
                      />
                      <div className="flex justify-end">
                        <PrimaryActionButton
                          type="button"
                          onClick={handleSubmit}
                          disabled={isSending || !prompt.trim()}
                          className="inline-flex gap-2"
                        >
                          Send
                          <ArrowUpRight className="h-4 w-4" />
                        </PrimaryActionButton>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </section>
          ) : null}
        </div>
      </section>
    </main>
  );
}
