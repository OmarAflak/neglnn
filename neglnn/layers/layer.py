from dataclasses import dataclass, field
from typing import Callable, Optional
from neglnn.network.state import Stateful
from neglnn.initializers.initializer import Initializer
from neglnn.optimizers.optimizer import Optimizer, Update
from neglnn.utils.types import Array, Shape
from neglnn.utils.identifiable import Identifiable

@dataclass
class BackwardState:
    input_gradient: Array
    parameter_gradients: tuple[Array, ...] = field(default_factory=tuple)

"""
Base Laye class. Initialization order is the following:
- `on_state`
- `on_initializer`
- `on_optimizer`
"""
class Layer(Stateful, Identifiable):
    def __init__(
        self,
        input_shape: Optional[Shape] = None,
        output_shape: Optional[Shape] = None,
        trainable: bool = False
    ):
        super().__init__()
        self.input_shape = input_shape
        self.output_shape = output_shape
        self.trainable = trainable

    def on_initializer(self, initializer: Initializer):
        """
        Initialize the trainable parameters here using the `initializer`
        """
        raise NotImplementedError

    def on_optimizer(self, provider: Callable[[], Optimizer]):
        self.optimizers: list[Optimizer] = []
        for parameter in self.parameters():
            optimizer = provider()
            optimizer.on_state(self.state)
            optimizer.on_target_shape(parameter.shape)
            self.optimizers.append(optimizer)

    def forward(self, input: Array) -> Array:
        raise NotImplementedError

    def backward(self, output_gradient: Array) -> BackwardState:
        """
        Return the input gradient as well as the parameters gradients.
        Parameters gradients must be returned in the same order as the
        parameters are returned in `parameters()`
        """
        raise NotImplementedError

    def parameters(self) -> tuple[Array, ...]:
        """
        Return a tuple of all the trainable parameters
        """
        raise NotImplementedError

    def optimize(self, gradients: tuple[Array, ...]):
        for optimizer, parameter, gradient in zip(
            self.optimizers,
            self.parameters(),
            gradients
        ):
            optimizer.record(Update(parameter, gradient))
            if optimizer.should_optimize():
                optimizer.optimize()