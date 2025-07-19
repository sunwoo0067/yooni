import * as React from "react"
import { format } from "date-fns"
import { Button } from "@/components/ui/button"

export interface DateRange {
  from: Date | undefined
  to?: Date | undefined
}

interface DatePickerWithRangeProps {
  date?: DateRange
  onSelect?: (date: DateRange | undefined) => void
  className?: string
}

export function DatePickerWithRange({
  date,
  onSelect,
  className,
}: DatePickerWithRangeProps) {
  const [selectedRange, setSelectedRange] = React.useState<DateRange>({
    from: date?.from,
    to: date?.to,
  })

  const handleDateChange = (type: 'from' | 'to', value: string) => {
    const newDate = value ? new Date(value) : undefined
    const newRange = {
      ...selectedRange,
      [type]: newDate,
    }
    setSelectedRange(newRange)
    onSelect?.(newRange)
  }

  return (
    <div className={`flex gap-2 ${className}`}>
      <div className="flex items-center gap-2">
        <label htmlFor="date-from" className="text-sm">From:</label>
        <input
          id="date-from"
          type="date"
          value={selectedRange.from ? format(selectedRange.from, 'yyyy-MM-dd') : ''}
          onChange={(e) => handleDateChange('from', e.target.value)}
          className="rounded-md border border-input bg-background px-3 py-2 text-sm"
        />
      </div>
      <div className="flex items-center gap-2">
        <label htmlFor="date-to" className="text-sm">To:</label>
        <input
          id="date-to"
          type="date"
          value={selectedRange.to ? format(selectedRange.to, 'yyyy-MM-dd') : ''}
          onChange={(e) => handleDateChange('to', e.target.value)}
          className="rounded-md border border-input bg-background px-3 py-2 text-sm"
        />
      </div>
    </div>
  )
}