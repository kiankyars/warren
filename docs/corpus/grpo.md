# GRPO notes

Group Relative Policy Optimization estimates advantages inside a group of rollouts from the same prompt instead of a learned critic.

A frozen reference policy plus an explicit KL term is the usual stability knob. If reward vs KL was never plotted, swapping GRPO for PPO will not tell you whether the run was under-regularized.

Delayed reference updates (every k optimizer steps) are a common unfinished item in small-policy checklists. Group size 8 is a reasonable default before touching k.
