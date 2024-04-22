import expt
print("expt:", expt.__version__)


path = "D:/Desktop/code/Discrete SAC analysis/results/MiniGrid-FourRooms-v0/kl_sac/100/230804-130057"
print(path)

print(expt.__file__)

run  = expt.get_runs(path)[0]

print(run.df)