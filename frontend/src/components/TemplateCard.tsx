import { Card, CardContent } from "@/components/ui/card";

type TemplateCardProps = {
  title: string;
  description: string;
};

export function TemplateCard({ title, description }: TemplateCardProps) {
  return (
    <Card className="group rounded-xl border border-border shadow-card hover:-translate-y-0.5 hover:shadow-input">
      <CardContent className="space-y-2 p-6">
        <h3 className="text-base font-medium text-foreground">{title}</h3>
        <p className="text-sm text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  );
}
