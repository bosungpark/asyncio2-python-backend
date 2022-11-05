from datetime import date
from typing import Optional, List

from allocation.domain.exceptions import OutOfStock
from allocation.domain.schemas import OrderLine
from allocation.domain.types import Reference, SKU, Quantity


class Batch:
    def __init__(self, ref: Reference, sku: SKU, qty: Quantity, eta: Optional[date]):
        self.reference=ref
        self.sku=sku
        self.eta=eta
        self._purchased_quantity=qty
        self._allocations=set()

    def allocate(self, line:OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line:OrderLine):
        if self.can_allocate(line):
            self._allocations.remove(line)

    @property
    def allocated_quantity(self)->int:
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity-self.allocated_quantity

    def can_allocate(self,line:OrderLine)->bool:
        return self.sku==line.sku and self.available_quantity>=line.qty

    def __eq__(self, other):
        if not isinstance(other, Batch):
            return False
        return other.reference==self.reference

    def __hash__(self):
        return hash(self.reference)

    def __gt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta>other.eta

class Product:
    def __init__(self, sku: str, batches: List[Batch], version_number: int = 0):
        self.sku = sku
        self.batches = batches
        self.version_number = version_number

    def allocate(self, line: OrderLine) -> str:
        try:
            batch = next(b for b in sorted(self.batches) if b.can_allocate(line))
            batch.allocate(line)
            self.version_number += 1
            return batch.reference
        except StopIteration:
            raise OutOfStock(f"Out of stock for sku {line.sku}")