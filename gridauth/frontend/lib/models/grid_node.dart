// lib/models/grid_node.dart

/// A single node in the grid authentication interface.
/// 
/// Client-side model — contains only what the server returns:
/// a node index and K character options. No role information.
class GridNode {
  final int nodeIndex;
  final List<String> chars;

  const GridNode({required this.nodeIndex, required this.chars});

  factory GridNode.fromJson(Map<String, dynamic> json) {
    return GridNode(
      nodeIndex: json['node_index'] as int,
      chars: List<String>.from(json['chars'] as List),
    );
  }
}
