import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CalendarCheck } from "lucide-react";

export function AppointmentView() {
  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-2xl font-semibold tracking-tight">Appointments</h2>
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="w-full rounded-2xl border border-border shadow-card">
          <CardContent className="p-6">
            <h3 className="mb-2 text-base font-medium">Upcoming</h3>
            <p className="text-sm text-muted-foreground">No upcoming appointments.</p>
          </CardContent>
        </Card>
        <Card className="w-full rounded-2xl border border-border shadow-card">
          <CardContent className="p-6">
            <h3 className="mb-2 text-base font-medium">Past</h3>
            <p className="text-sm text-muted-foreground">No past appointments.</p>
          </CardContent>
        </Card>
      </div>
      <Card className="w-full max-w-xl rounded-2xl border border-border shadow-card">
        <CardContent className="flex flex-col items-center justify-center gap-4 p-8 text-center">
          <CalendarCheck className="h-12 w-12 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">Book an appointment from Chat after we find the right provider for you.</p>
          <Button type="button" variant="outline" className="rounded-full" disabled>
            Book an appointment
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
