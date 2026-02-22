import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

const HARDCODED_PROFILE = {
  name: "John Smith",
  email: "john.smith@example.com",
  dateOfBirth: "1993-03-15",
  zip: "30332",
  phone: "(912) 224-2661",
};

const HARDCODED_HISTORY = [
  { date: "2025-02-10", type: "Visit", title: "Allergies consultation", detail: "New patient visit — follow-up scheduled." },
  { date: "2025-01-22", type: "Lab", title: "Routine labs", detail: "CBC, metabolic panel. Results within normal limits." },
  { date: "2024-11-05", type: "Visit", title: "Annual physical", detail: "Preventive visit. No acute issues." },
  { date: "2024-08-12", type: "Condition", title: "Seasonal allergies", detail: "Ongoing. Flonase as needed." },
  { date: "2024-03-15", type: "Visit", title: "Wellness check", detail: "Blood pressure 118/76. Discussed diet and exercise." },
];

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium text-foreground">{value}</span>
    </div>
  );
}

function HistoryItem({
  date,
  type,
  title,
  detail,
  isLast,
}: {
  date: string;
  type: string;
  title: string;
  detail: string;
  isLast: boolean;
}) {
  const formattedDate = new Date(date + "T00:00:00").toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <div className="h-3 w-3 shrink-0 rounded-full border-2 border-primary bg-background" />
        {!isLast && <div className="mt-1 h-full min-h-[24px] w-px bg-border" />}
      </div>
      <div className="flex-1 pb-6">
        <div className="flex flex-wrap items-baseline gap-2">
          <span className="text-sm font-medium text-foreground">{title}</span>
          <span className="text-xs text-muted-foreground">{formattedDate}</span>
          <span className="rounded bg-muted px-1.5 py-0.5 text-xs font-medium text-muted-foreground">
            {type}
          </span>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">{detail}</p>
      </div>
    </div>
  );
}

export function ProfileView() {
  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-2xl font-semibold tracking-tight">Profile</h2>
      <div className="flex flex-col items-stretch gap-6 md:flex-row md:items-start">
        <Card className="w-full max-w-sm shrink-0 rounded-2xl border border-border shadow-card md:shrink-0">
          <CardContent className="space-y-4 p-6">
            <Field label="Name" value={HARDCODED_PROFILE.name} />
            <Field label="Email" value={HARDCODED_PROFILE.email} />
            <Field label="Date of birth" value={HARDCODED_PROFILE.dateOfBirth} />
            <Field label="Zip" value={HARDCODED_PROFILE.zip} />
            <Field label="Phone" value={HARDCODED_PROFILE.phone} />
          </CardContent>
        </Card>

        <Card className="min-w-0 flex-1 rounded-2xl border border-border shadow-card">
          <CardContent className="p-6">
            <h3 className="text-lg font-medium tracking-tight">Patient history</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Visits, labs, and conditions in one place (MyChart-style). Demo data below.
            </p>
            <div className="relative mt-4">
              {HARDCODED_HISTORY.map((item, i) => (
                <HistoryItem
                  key={`${item.date}-${item.title}`}
                  date={item.date}
                  type={item.type}
                  title={item.title}
                  detail={item.detail}
                  isLast={i === HARDCODED_HISTORY.length - 1}
                />
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
