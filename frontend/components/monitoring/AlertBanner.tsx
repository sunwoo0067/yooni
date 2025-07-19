import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AlertCircle, AlertTriangle, X } from 'lucide-react';
import { useState } from 'react';

interface AlertItem {
  id: string;
  severity: 'warning' | 'critical' | 'info';
  title: string;
  message: string;
  timestamp: Date;
}

interface AlertBannerProps {
  alerts: AlertItem[];
  onDismiss?: (id: string) => void;
}

export function AlertBanner({ alerts, onDismiss }: AlertBannerProps) {
  const [dismissedAlerts, setDismissedAlerts] = useState<Set<string>>(new Set());
  
  const visibleAlerts = alerts.filter(alert => !dismissedAlerts.has(alert.id));
  
  if (visibleAlerts.length === 0) return null;
  
  const handleDismiss = (id: string) => {
    setDismissedAlerts(prev => new Set(prev).add(id));
    onDismiss?.(id);
  };
  
  const getAlertStyle = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'destructive';
      case 'warning':
        return 'warning';
      default:
        return 'default';
    }
  };
  
  const getAlertIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <AlertCircle className="h-4 w-4" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4" />;
      default:
        return <AlertCircle className="h-4 w-4" />;
    }
  };
  
  return (
    <div className="space-y-2">
      {visibleAlerts.map(alert => (
        <Alert key={alert.id} variant={getAlertStyle(alert.severity)}>
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-2">
              {getAlertIcon(alert.severity)}
              <div className="flex-1">
                <AlertTitle>{alert.title}</AlertTitle>
                <AlertDescription className="mt-1">
                  {alert.message}
                  <span className="text-xs ml-2 opacity-70">
                    ({new Date(alert.timestamp).toLocaleTimeString()})
                  </span>
                </AlertDescription>
              </div>
            </div>
            <button
              onClick={() => handleDismiss(alert.id)}
              className="ml-4 p-1 hover:opacity-70"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </Alert>
      ))}
    </div>
  );
}