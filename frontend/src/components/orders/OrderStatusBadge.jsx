import { CheckCircle2, Clock, XCircle } from 'lucide-react'
import { Badge } from '@/components/ui'

export default function OrderStatusBadge({ status }) {
  if (status === 'paid') {
    return (
      <Badge tone="success" icon={<CheckCircle2 className="w-3.5 h-3.5" />}>
        已支付
      </Badge>
    )
  }
  if (status === 'cancelled') {
    return (
      <Badge tone="default" icon={<XCircle className="w-3.5 h-3.5" />}>
        已取消
      </Badge>
    )
  }
  if (status === 'refunded') {
    return <Badge tone="info">已退款</Badge>
  }
  return (
    <Badge tone="warning" icon={<Clock className="w-3.5 h-3.5" />}>
      待支付
    </Badge>
  )
}
