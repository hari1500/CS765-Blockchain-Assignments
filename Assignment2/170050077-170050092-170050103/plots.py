import matplotlib.pyplot as plt

time = [0.25, 0.5, 1, 2]
mvps = [[0.9652413305, 0.9890480638, 0.9954891323, 1], [0.9849690539, 0.9974747475, 0.9980806142, 1], [0.9810682894, 0.9889139974, 0.996310169, 0.996835443]]
adversary_fractions = [[0.4659249255, 0.3925735147, 0.3570347958, 0.3582089552], [0.3953279425, 0.3776932826, 0.3699421965, 0.3501577287], [0.3972413793, 0.359314319, 0.3506493506, 0.356687898]]

plt.xlabel("Time")
plt.ylabel("Mining Power Utilization")
plt.title("Mining Power Utilization vs Time at 10 percent of nodes flooded")
plt.plot([0.125, 0.25, 0.5, 1], mvps[0], marker='+')
plt.savefig('mvp_10.png')
plt.close()

plt.xlabel("Time")
plt.ylabel("Mining Power Utilization")
plt.title("Mining Power Utilization vs Time at 20 percent of nodes flooded")
plt.plot(time, mvps[1], marker='+')
plt.savefig('mvp_20.png')
plt.close()

plt.xlabel("Time")
plt.ylabel("Mining Power Utilization")
plt.title("Mining Power Utilization vs Time at 30 percent of nodes flooded")
plt.plot(time, mvps[2], marker='+')
plt.savefig('mvp_30.png')
plt.close()

plt.xlabel("Time")
plt.ylabel("Adversary's fraction")
plt.title("Adversary's fraction in main chain vs Time at 10 percent of nodes flooded")
plt.plot([0.125, 0.25, 0.5, 1], adversary_fractions[0], marker='+')
plt.savefig('adv_frac_10.png')
plt.close()

plt.xlabel("Time")
plt.ylabel("Adversary's fraction")
plt.title("Adversary's fraction in main chain vs Time at 20 percent of nodes flooded")
plt.plot(time, adversary_fractions[1], marker='+')
plt.savefig('adv_frac_20.png')
plt.close()

plt.xlabel("Time")
plt.ylabel("Adversary's fraction")
plt.title("Adversary's fraction in main chain vs Time at 30 percent of nodes flooded")
plt.plot(time, adversary_fractions[2], marker='+')
plt.savefig('adv_frac_30.png')
plt.close()
