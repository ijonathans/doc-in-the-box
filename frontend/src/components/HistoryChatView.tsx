import { Card, CardContent } from "@/components/ui/card";

const HARDCODED_SESSIONS = [
  { id: "1", title: "Headache inquiry", date: "Feb 20, 2026" },
  { id: "2", title: "Rash follow-up", date: "Feb 19, 2026" },
  { id: "3", title: "General check-in", date: "Feb 18, 2026" },
];

export function HistoryChatView() {
  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-2xl font-semibold tracking-tight">History Chat</h2>
      <div className="space-y-3">
        {HARDCODED_SESSIONS.map((session) => (
          <Card
            key={session.id}
            className="w-full max-w-xl cursor-pointer rounded-2xl border border-border shadow-card transition-shadow hover:shadow-input"
          >
            <CardContent className="flex flex-row items-center justify-between p-4">
              <span className="text-sm font-medium text-foreground">{session.title}</span>
              <span className="text-xs text-muted-foreground">{session.date}</span>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
