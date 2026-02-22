import { Card, CardContent } from "@/components/ui/card";

const HARDCODED_PROFILE = {
  name: "John Smith",
  email: "john.smith@example.com",
  dateOfBirth: "1993-03-15",
  zip: "30332",
  phone: "(912) 224-2661",
};

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium text-foreground">{value}</span>
    </div>
  );
}

export function ProfileView() {
  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-2xl font-semibold tracking-tight">Profile</h2>
      <Card className="w-full max-w-xl rounded-2xl border border-border shadow-card">
        <CardContent className="space-y-4 p-6">
          <Field label="Name" value={HARDCODED_PROFILE.name} />
          <Field label="Email" value={HARDCODED_PROFILE.email} />
          <Field label="Date of birth" value={HARDCODED_PROFILE.dateOfBirth} />
          <Field label="Zip" value={HARDCODED_PROFILE.zip} />
          <Field label="Phone" value={HARDCODED_PROFILE.phone} />
        </CardContent>
      </Card>
    </div>
  );
}
