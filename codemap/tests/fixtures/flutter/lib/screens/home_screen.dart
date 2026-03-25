import '../models/order.dart';
import '../widgets/order_card.dart';

class HomeScreen extends StatelessWidget {
  final List<Order> orders = [];

  Widget build() {
    return OrderCard(order: orders.first);
  }
}
