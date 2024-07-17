from typing import Callable, Type

import torch as T
from torch import nn, optim
from torch.nn import functional as F
from torch.utils.data import DataLoader, Dataset


def RMSE_loss(input: T.Tensor, target: T.Tensor) -> T.Tensor:
    return T.sqrt(F.mse_loss(input, target))


def train_model(
    model: nn.Module,
    datasets: dict[str, Dataset],
    optimizer: Type[optim.Optimizer] = optim.SGD,
    loss_fn: Callable = nn.MSELoss(),
    epochs: int = 500,
    lr: float = 1e-2,
    batch_size: int = 8,
    eval_loss_fn: Callable = RMSE_loss,
    eval_batch_size: int = 32,
    logging_freq: int = 100,
) -> dict[str, list[float]]:
    model_optimizer = optimizer(model.parameters(), lr=lr)  # type: ignore

    train_dataset = datasets["train"]
    train_dataloader = DataLoader(train_dataset, batch_size)
    eval_dataloaders = {
        n: DataLoader(d, eval_batch_size) for n, d in datasets.items() if n != "train"
    }
    results: dict[str, list[float]] = {d: [] for d in datasets.keys()}

    rolling_loss = 0
    iteration = 0

    for epoch in range(epochs):
        for X_batch, Y_batch in train_dataloader:
            Y_pred = model(X_batch)
            loss = loss_fn(Y_batch, Y_pred)
            loss.backward()

            eval_loss = eval_loss_fn(Y_batch, Y_pred).item()
            if iteration == 0:
                rolling_loss = eval_loss
            else:
                n = min(iteration, logging_freq)
                rolling_loss = (rolling_loss * (n - 1) + eval_loss) / n

            model_optimizer.step()
            model_optimizer.zero_grad()

            iteration += 1

            if iteration % logging_freq == 0:
                results["train"].append(rolling_loss)

                with T.no_grad():
                    for name, dataloader in eval_dataloaders.items():
                        losses = []
                        for X_batch, Y_batch in dataloader:
                            Y_pred = model(X_batch)
                            loss = eval_loss_fn(Y_batch, Y_pred)
                            losses.append(loss.item())

                        results[name].append(sum(losses) / len(losses))

    return results
