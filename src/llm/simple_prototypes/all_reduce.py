import torch
import torch.distributed as dist
import torch.multiprocessing as mp
import os

def setup(rank, world_size):
    
    # Variables are standard for torch.distributed initialization
    os.environ['MASTER_ADDR'] = 'localhost'
    os.environ['MASTER_PORT'] = '12355'

    # Initialize the process group
    # Backend 'gloo' works on CPU/Mac, 'nccl' is for NVIDIA GPUs
    print(f"Rank {rank} Initializing process group with backend 'gloo'...")
    dist.init_process_group("gloo", rank=rank, world_size=world_size)
    print(f"Rank {rank}: Process group initialized.")


def cleanup():
    dist.destroy_process_group()
    print("Process group destroyed.")

def run_all_reduce(rank, world_size):
    setup(rank, world_size)

    # Determine device: Use MPS if available for tensor creation,
    # but Gloo communication happens via CPU memory.
    # all-reduce is not supported on MPS yet so decided to go 
    # ahead with the cpu.
    device = torch.device("cpu")
    print("Warning: MPS not available, using CPU.")

    tensor = torch.tensor([float(rank + 1)], device=device)
    print(f"Rank {rank}: Tensor before All-Reduce: {tensor.item():.1f} on device {tensor.device}")

    if world_size > 1:

        # Ensures that all the processes are have finished their setup
        # before any of them start the potentially time consuming all_reduce operation.
        # It helps synchronize the starting point of the collective operation across
        # all the processes.
        dist.barrier()
        print(f"Rank {rank}: Barrier passed, performing All-Reduce...")

    if world_size > 1:
        dist.all_reduce(tensor, op=dist.ReduceOp.SUM)
    else:
        print(f"Rank {rank}: Skipping All-Reduce (world_size=1)")

    if world_size > 1:
        # Ensures that all the processes have successfully completed the all_reduce
        # operation before any of them proceed with the next step. This prevents race
        # conditions where one proceses might try to take the result of the all_reduce
        # before another process has finished contributing to it or receiving it.
        dist.barrier()

    print(f"Rank {rank}: Tensor after All-Reduce (Sum): {tensor.item():.1f} on device {tensor.device}")

    cleanup()

if __name__ == "__main__":
    world_size = 4
    print(f"Spawning {world_size} processes...")
    
    # Creating the desired number of processes, running the unified specified function in each process
    # assigns a unique rank to each process and passes it automatically to the function, passing any
    # other shared information and join to wait for all the process to complete.
    mp.spawn(run_all_reduce, args=(world_size,), nprocs=world_size, join=True)
    print("All processes finished.") 
