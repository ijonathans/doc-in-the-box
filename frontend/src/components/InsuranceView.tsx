import { Card, CardContent } from "@/components/ui/card";

const HARDCODED_INSURANCE = {
  planName: "Acme Health PPO",
  memberId: "MEM-2024-XXXX",
  group: "GRP-001",
  status: "Active",
};

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium text-foreground">{value}</span>
    </div>
  );
}

export function InsuranceView() {
  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-2xl font-semibold tracking-tight">Insurance</h2>
      <Card className="w-full max-w-xl rounded-2xl border border-border shadow-card">
        <CardContent className="space-y-4 p-6">
          <Field label="Plan name" value={HARDCODED_INSURANCE.planName} />
          <Field label="Member ID" value={HARDCODED_INSURANCE.memberId} />
          <Field label="Group" value={HARDCODED_INSURANCE.group} />
          <Field label="Status" value={HARDCODED_INSURANCE.status} />
        </CardContent>
      </Card>
    </div>
  );
}
