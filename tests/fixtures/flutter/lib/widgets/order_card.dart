import '../models/order.dart';

class OrderCard extends StatelessWidget {
  final Order order;

  OrderCard({required this.order});

  Widget build() {
    return Text(order.id);
  }
}
