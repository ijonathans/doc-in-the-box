import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

const HARDCODED_INSURANCE = {
  planName: "UnitedHealthcare Choice Plus POS",
  memberId: "7994822",
  group: "UHCSTRC01",
  status: "Active",
};

const HARDCODED_ZOCDOC = {
  connected: true,
  accountEmail: "john.smith@example.com",
  linkedSince: "Jan 15, 2025",
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

      <div className="flex flex-col gap-3">
        <h3 className="text-lg font-medium tracking-tight">ZocDoc</h3>
        <Card className="w-full max-w-xl rounded-2xl border border-border shadow-card">
          <CardContent className="p-6">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-col gap-1">
                <span className="text-sm font-medium text-foreground">Account connection</span>
                <span className="text-sm text-muted-foreground">
                  {HARDCODED_ZOCDOC.connected
                    ? `Connected as ${HARDCODED_ZOCDOC.accountEmail}`
                    : "Not connected"}
                </span>
              </div>
              {HARDCODED_ZOCDOC.connected && (
                <Badge variant="secondary" className="shrink-0">
                  Connected
                </Badge>
              )}
            </div>
            {HARDCODED_ZOCDOC.connected && (
              <>
                <Separator className="my-4" />
                <div className="flex flex-col gap-2 text-sm text-muted-foreground">
                  <span>Linked since {HARDCODED_ZOCDOC.linkedSince}</span>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
