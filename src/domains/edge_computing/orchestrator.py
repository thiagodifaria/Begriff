import ray
from typing import List, Dict, Any
from src.domains.edge_computing.nodes import EdgeComputeNode

class EdgeOrchestrator:
    """
    Manages a pool of edge compute nodes and dispatches tasks to them.
    """
    def __init__(self):
        """
        Initializes Ray and creates a pool of edge nodes.
        """
        ray.init(ignore_reinit_error=True)
        self.nodes = {
            "sa-east-1": EdgeComputeNode.remote(region="sa-east-1"),  # São Paulo
            "us-east-1": EdgeComputeNode.remote(region="us-east-1"),  # N. Virginia
        }

    def dispatch_preprocessing_task(self, transactions: List[Dict[str, Any]], user_location: str = "sa-east-1") -> dict:
        """
        Dispatches a preprocessing task to the nearest edge node.
        """
        if user_location not in self.nodes:
            # Default to a fallback node if the user's location is not supported
            user_location = "us-east-1"

        # Get the handle to the appropriate edge node
        node = self.nodes[user_location]

        # Call the actor's method remotely
        future = node.preprocess_transactions.remote(transactions)

        # Wait for and retrieve the result
        result = ray.get(future)

        return result

    def shutdown(self):
        """
        Shuts down the Ray instance.
        """
        ray.shutdown()