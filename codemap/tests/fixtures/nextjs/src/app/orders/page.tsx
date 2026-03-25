import { OrderCard } from "../../components/OrderCard";

export default function OrdersPage() {
  return (
    <main>
      <OrderCard order={{ id: "1", total: 100 }} />
    </main>
  );
}
