---
layout: single
title: "Literature Review: Dual-Arm Robotic Coordination"
header:
  teaser: /assets/images/posts/lit_review.png
date: 2026-03-05
classes: wide
author_profile: false
---



## 1. Background

### 1.1 Industrial and Commercial Rationale

The operational case for dual-arm robotic systems is well-documented. [Marvel, Bostelman, and Falco (2014)](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=919247) catalogued assembly task categories for which single-arm systems are insufficient: objects exceeding the reachable envelope of a single manipulator, operations requiring simultaneous positioning of two components, and throughput requirements that sequential operation cannot satisfy.

[Peta, Wiśniewski, Kotarski, and Ciszak (2025)](https://doi.org/10.3390/app15062976) provided the most rigorous comparative study, measuring a dual-arm configuration against a single-arm baseline on identical precision assembly tasks. The dual-arm configuration achieved a cycle time of 13.6 seconds versus 20.6 seconds that's a 34% reduction with a positive return on investment within eight months. [Pantanetti et al. (2024)](https://doi.org/10.1109/MESA61532.2024.10704820) corroborated this at a manufacturing case-study level, documenting throughput and dexterity gains from transitioning a production cell from single-arm to dual-arm collaborative operation. [Buhl et al. (2019)](https://doi.org/10.1016/j.promfg.2020.01.043) and [Smith et al. (2012)](https://doi.org/10.1016/j.robot.2012.07.005) provide earlier grounding, with Smith et al.'s survey of dual-arm manipulation covering the full landscape of coordination approaches developed through 2012.

At the research frontier, [Tian et al. (2025)](https://doi.org/10.48550/arXiv.2506.05168) demonstrated 80% real-world success on assemblies of five or more parts using an integrated dual-arm planning and learning system (Fabrica), recognised with the Best Paper Award at CoRL 2025.

### 1.2 Fundamental Technical Challenges

Deploying two manipulators in a shared workspace introduces three challenges that extend beyond the single-arm case.

**Challenge 1: Native Independent Control Stacks.** [Verma and Ranga (2021)](https://doi.org/10.1007/s10846-021-01378-2), in a comprehensive taxonomy of multi-robot coordination, document independent operation as the architectural default: coupling between agents is absent unless explicitly engineered. [Peron, Nan Fernandez-Ayala, Vlahakis, and Dimarogonas (2025)](https://doi.org/10.48550/arXiv.2502.16531) showed through formal treatment of multi-robot synchronisation under linear temporal logic specifications that temporal coordination guarantees require active architectural provision and cannot be assumed to emerge from component behaviour.

**Challenge 2: Collision Risk in Shared Operational spaces.** [Claes and Tuyls (2018)](https://doi.org/10.1007/s10514-018-9726-5) established that the standard single-robot assumption, that the environment is either static or occupied by independently moving obstacles, is insufficient when multiple manipulators move simultaneously through an overlapping volume. Treating a co-manipulator as a static collision body during planning is valid only when sequential execution is enforced. The volume of recent publication activity on inter-arm collision avoidance, including [Zhang and Jia (2026)](https://doi.org/10.1007/s11465-026-0873-7), [Shukla et al. (2025)](https://doi.org/10.3389/frobt.2025.1604506), and [Kaypak et al. (2025)](https://doi.org/10.48550/arXiv.2503.11791), indicates this remains an active area of investigation.

**Challenge 3: Absence of a Standardised Hardware-Software Integration Pattern.** When two manipulators are deployed within a Robot Operating System 2 (ROS2) environment, each hardware driver publishes joint state information to an isolated namespace using generic joint identifiers. Motion planning infrastructure requires a unified joint state representation with distinct identifiers across both arms. No standardised mechanism for this namespace-to-planning translation is provided by the ROS2 or MoveIt2 frameworks. [Macenski et al. (2022)](https://doi.org/10.1126/scirobotics.abm6074) document namespace isolation as a foundational ROS2 design principle. Practitioner discourse on the resulting integration challenge remains active: MoveIt2 GitHub issues such as [#465 (2020)](https://github.com/moveit/moveit_tutorials/issues/465) and[#3037 (2024)](https://github.com/moveit/moveit2/issues/3037), both requesting native multi-arm coordination support, were closed without a standard solution.

---

## 2. Motion Planning Architecture

### 2.1 The Centralised vs. Decoupled Question

The primary architectural choice in multi-arm motion planning is whether to treat the system as a single composite robot reasoning over a unified high-dimensional configuration space (centralised planning), or to maintain independent per-arm planners whose outputs are subsequently coordinated (decoupled planning). The prevailing assumption held that centralised planning was computationally intractable for dual-arm systems due to exponential growth of the configuration space. A dual six-degree-of-freedom system occupies a 12-dimensional configuration space, leading to a general preference for decoupled formulations in practical deployments.

[Shome, Solovey, Dobson, Halperin, and Bekris (2019)](https://doi.org/10.1007/s10514-019-09832-9) addressed the tractability concern algorithmically, presenting dRRT*, an asymptotically optimal multi-robot motion planning algorithm that decomposes the joint planning problem into lower-dimensional subproblems while preserving probabilistic completeness guarantees.

[Sucan and Moll (2012)](https://doi.org/10.1109/MRA.2012.2205651) described the Open Motion Planning Library (OMPL), which provides the algorithmic foundation for the majority of ROS-based manipulation planning. OMPL implements RRTConnect, PRM, RRT*, and KPIECE, among other sampling-based algorithms, all probabilistically complete. [Kuffner and LaValle (2000)](https://doi.org/10.1109/ROBOT.2000.844730) introduced RRTConnect specifically as a bidirectional tree extension offering efficient single-query path planning that remains the practical default in manipulation contexts. [Orthey and Kavraki (2024)](https://doi.org/10.1146/annurev-control-061623-094742) provide a comprehensive comparative review of sampling-based planning algorithms, confirming that RRTConnect remains a practically competitive default and characterising convergence properties across configuration space dimensionalities.

### 2.2 Centralised Planning Validation

The foundational empirical challenge to assumed decoupled planning superiority is presented by [Wittmann, Ochsenfarth, Sonneville, and Rixen (2024)](https://doi.org/10.1007/s10846-024-02175-3) in the *Journal of Intelligent and Robotic Systems*. Their study constitutes the first controlled comparison of both architectural approaches on physical dual-arm hardware, using two seven-degree-of-freedom Franka Emika Panda arms executing a standardised scenario set under the MoveIt motion planning framework with RRT* as the planning algorithm.

The results were contrary to prior assumptions:

| Metric | Centralised (12-DOF) | Decoupled (2 × 6-DOF) |
|---|---|---|
| Mean planning time | 1.2–1.8 s | 2.1–3.2 s |
| Planning success rate | 99.2–99.9% | 70–80% |
| Deadlock incidence | Low | Frequent in constrained configurations |
| Path quality | Globally coordinated | Requires post-hoc optimisation |

The ~25 percentage point success rate differential is attributable to the deadlock pathology inherent in decoupled planning: each arm's independently generated plan may be locally valid while the combined execution state produces a configuration in which each arm is blocked by the trajectory of the other. Centralised planning, by reasoning over the combined 12-DOF configuration space, structurally prevents this failure mode.

### 2.3 Asynchronous Execution Within a Dual-Arm Setup

The Wittmann et al. result addresses the planning layer. A complementary body of work addresses the execution layer, specifically the case in which task requirements do not necessitate temporal coupling between arms.

[Stoop, Ratnayake, and Toffetti (2024)](https://doi.org/10.1109/ICRA57147.2024.10611498), presented at IEEE ICRA 2024, demonstrated independent arm trajectories with non-coupled timing within the MoveIt2 ecosystem, reporting execution time reductions proportional to the fraction of task time amenable to parallel operation. A critical limitation is the reactive character of their collision avoidance: potential inter-arm collisions are detected during trajectory execution and managed through a backlog or replanning mechanism. This provides weaker safety guarantees than planning-time avoidance.

[Agarwal et al. (2023)](https://doi.org/10.48550/arXiv.2309.10164) present a scalable multi-robot framework for decentralised and asynchronous perception-action-communication loops, providing architectural patterns for asynchronous coordination that are transferable to the bimanual manipulation domain. [Celik, Rodriguez, Ayestaran, and Yavuz (2024)](https://doi.org/10.3390/s24165382) demonstrate that deterministic coordination can be maintained in the absence of a shared physical clock under appropriate communication conditions.

---

## 3. Collision Avoidance Architecture

### 3.1 Planning-Time Geometric Avoidance

Planning-time geometric avoidance integrates collision checking directly into the trajectory generation process. The motion planner maintains a geometric model of the robot derived from a Unified Robot Description Format (URDF) specification. Each configuration sampled during planning is evaluated for geometric collision before exploration proceeds; trajectories that pass planning validation are collision-free by construction.

The collision checking infrastructure underlying MoveIt is provided by the Flexible Collision Library (FCL), introduced by [Pan, Chitta, and Manocha (2012)](https://doi.org/10.1109/ICRA.2012.6225337). FCL implements proximity queries using bounding volume hierarchies, enabling computationally tractable continuous collision checking within planning pipelines. [Coleman, Sucan, Chitta, and Correll (2014)](https://doi.org/10.48550/arXiv.1404.3785) describe the MoveIt architecture built on FCL, adopted across more than 1,000 manipulation deployments.

Two implementation choices substantially affect practical performance. First, conservative geometric padding, typically five centimetres per link, establishes a safety margin that absorbs modelling uncertainty, calibration error, and trajectory tracking deviation, providing the formal geometric safety guarantee. Second, a collision matrix pre-classifies link pairs as requiring active checking or as permanently non-colliding, reducing the number of active proximity queries by approximately 75%.

[Montaut, Le Lidec, Petrík, Sivic, and Carpentier (2023)](https://doi.org/10.1109/TRO.2024.3350183) present GJK++, an accelerated implementation of the Gilbert-Johnson-Keerthi distance algorithm providing reduced per-query latency within the same geometric paradigm. [Zhu et al. (2024)](https://doi.org/10.48550/arXiv.2409.14955) address the trade-off between conservative padding and accessible configuration space through tighter geometric approximations.

### 3.2 Reactive Runtime Avoidance

Reactive avoidance approaches detect proximity violations during trajectory execution and modify the ongoing motion in response. [Zhang and Jia (2026)](https://doi.org/10.1007/s11465-026-0873-7) develop a reactive collision-free motion generation framework for tightly coupled bimanual manipulation. [Shukla et al. (2025)](https://doi.org/10.3389/frobt.2025.1604506) present iAPF, an improved artificial potential field framework for inter-arm collision avoidance in asymmetric dual-arm configurations.

The principal advantage of reactive approaches is their capacity to respond to dynamic environmental conditions that planning-time methods cannot anticipate. Their fundamental limitation is that safety is characterised empirically rather than formally: effectiveness depends on sensor update rates, approach geometry, and dynamic response of the controller. The consensus in the deployment literature, reflected in the preponderance of industrial systems employing planning-time avoidance, is that reactive methods are appropriately characterised as a complementary execution-layer safeguard rather than a primary safety mechanism. [Claes and Tuyls (2018)](https://doi.org/10.1007/s10514-018-9726-5) state this explicitly.

### 3.3 Learning-Based Avoidance

Deep learning approaches to collision avoidance have emerged in the recent literature. [Lee, Luo, and Jung (2025)](https://doi.org/10.3390/s25226822) apply multi-agent deep reinforcement learning to collision-free posture control of co-located manipulators. [Kaypak, Wei, Krishnamurthy, and Khorrami (2025)](https://doi.org/10.48550/arXiv.2503.11791) incorporate learned geometric interaction models for safe multi-arm coordination.

The persistent methodological limitation is the simulation-to-reality performance gap: models trained in simulation exhibit degraded performance on physical hardware due to distributional shift. [Tian et al. (2025)](https://doi.org/10.48550/arXiv.2506.05168) document this gap explicitly: real-world task success rates are lower than simulation rates by a margin attributable to unmodelled environmental variation. For safety-critical manufacturing applications in which failure mode characterisation is a regulatory or operational requirement, empirical safety bounds are insufficient. This accounts for the limited real-world deployment of learning-based collision avoidance relative to the extensive deployment of planning-time geometric methods.

---

## 4. Execution Strategy

### 4.1 Taxonomy

The execution strategy problem concerns how arms coordinate temporally during task execution, given that planning-time collision avoidance has been satisfied. Three strategies are documented in the literature:

- **Sequential execution**: One arm completes its motion before the second commences. Collision risk at execution time is minimised by eliminating co-motion, at the cost of constraining throughput to the single-arm rate.
- **Synchronised parallel execution**: Both arms commence motion simultaneously from a shared trajectory plan, with matched temporal parameterisation ensuring concurrent waypoint arrival. Required for tasks imposing strict relative end-effector positioning constraints.
- **Asynchronous parallel execution**: Arms execute with independent timing, potentially commencing new sub-tasks while the co-manipulator is mid-trajectory. Throughput is maximised for tasks whose sub-tasks occupy spatially separated workspace regions.

[Dreher, Dormanns, Meixner, and Asfour (2026)](https://doi.org/10.48550/arXiv.2603.06538) advance the argument that the temporal relationship between arms is a task-intrinsic property that must be learned rather than pre-specified, representing the current frontier in understanding the relationship between task semantics and execution timing. Existing systems characteristically commit to one strategy at design time, imposing that strategy on all tasks regardless of their specific coordination requirements. This inflexibility is the structural limitation the literature identifies.

### 4.2 Synchronous Execution

[Zhang, Jin, Ge, and Zhao (2023)](https://doi.org/10.3390/s23115120) present a real-time kinematically synchronous planning algorithm for cooperative manipulation employing a self-organising competitive neural network to generate temporally matched joint trajectories. [Li et al. (2024)](https://doi.org/10.48550/arXiv.2403.08191) formulate synchronised dual-arm rearrangement as a cooperative multi-Travelling Salesman Problem, optimising task assignment and sequencing jointly. [Fu et al. (2025)](https://doi.org/10.1088/1742-6596/3019/1/012039) implement a synchronous control system incorporating digital twin technology for real-time monitoring of synchronisation fidelity during execution.


### 4.3 Asynchronous Execution

Beyond the contributions of Stoop et al. (2024) and Agarwal et al. (2023) discussed in Section 2.3, [Celik, Rodriguez, Ayestaran, and Yavuz (2024)](https://doi.org/10.3390/s24165382) investigate communication infrastructure for decentralised robot synchronisation, demonstrating that deterministic coordination can be maintained in the absence of a shared physical clock under appropriate communication conditions. [Abbas, Narayan, and Dwivedy (2023)](https://doi.org/10.1007/s41315-023-00292-0) provide a systematic review of cooperative dual-arm manipulators covering modelling, planning, control, and vision strategies, surveying the state of asynchronous coordination approaches through 2023.

### 4.4 Adaptive and Multi-Mode Strategy Selection

The extension of execution strategy from a fixed design-time parameter to a runtime-selectable variable has been investigated in adjacent domains. [Liu, Fani Sani et al. (2025)](https://doi.org/10.48550/arXiv.2510.00154) present RoboPilot, a dual-thinking mode framework comprising a fast reactive mode and a slow deliberative mode, with autonomous runtime selection mediated by a ModeSelector component. Evaluated on physical hardware, the adaptive mode selection mechanism increased error recovery rates from 0% under a fixed single-mode baseline to 86%, a result that empirically validates the utility of runtime strategy selection over static commitment. The architectural principle generalises: the performance improvement derives not from the individual modes, but from the capacity to select between them in response to task context.

[Silva et al. (2025)](https://doi.org/10.3389/frobt.2025.1517887) provide a formal theoretical foundation for runtime strategy adaptation in ROSA, a knowledge-based self-adaptive robotics framework. Task requirements and environmental constraints are encoded as a knowledge base; a continuous monitoring component evaluates execution context and triggers strategy transitions in response to detected condition changes.

Neither RoboPilot nor ROSA addresses the specific instantiation of this problem in dual-arm coordination: selection among synchronous, asynchronous, and hybrid execution modes based on spatial relationships between end-effectors and temporal coupling requirements of the manipulation task.

---

## 5. Industrial and Commercial Systems

The commercial dual-arm landscape is characterised by deep architectural commitment to single coordination modes, reflecting the optimisation requirements of high-volume production environments at the cost of operational flexibility.

**ABB YuMi** is a purpose-built industrial dual-arm robot deployed at production scale, with over 500 documented installations in automotive assembly and electronics manufacturing. Its monolithic proprietary architecture integrates both seven-degree-of-freedom arms under a unified firmware-level controller, providing centralised planning and synchronised execution with integrated force-torque sensing. Reported uptime exceeds 99% across documented deployments, establishing YuMi as the reliability benchmark for industrial dual-arm coordination. The architecture's limitation is the direct consequence of its strength: a single, fixed coordination mode optimised for its intended task portfolio, with no provision for asynchronous execution when synchronisation is operationally unnecessary. Algorithm transparency and task adaptation require vendor engagement via the proprietary RAPID programming environment, at acquisition costs of \$150K–\$250K that are prohibitive for flexible research and SME manufacturing contexts.

**MoveIt Pro** (PickNik Robotics) is the commercial extension of the open-source MoveIt2 framework, providing production-grade tooling including a visual Behaviour Tree editor, digital twin integration, and real-time execution monitoring. It constitutes the de facto standard for commercial manipulation deployments using MoveIt2. Its relevant limitation is that it is closed-source and does not provide native multi-mode execution coordination: synchronous, asynchronous, and hybrid execution are not built-in capabilities, and execution strategy selection is delegated to the implementing engineer. Multi-arm capability is available as a separate, separately priced add-on.

**Fabrica** ([Tian et al., 2025](https://doi.org/10.48550/arXiv.2506.05168)) represents the research frontier in dual-arm task planning, addressing automatic decomposition of multi-part assembly tasks from CAD models through integrated planning and learning. Its contribution is at the task-planning layer, determining what the arms should do and in what order. The execution layer, determining how arms should coordinate temporally during task execution, is outside its scope. Planning times of 15–45 seconds preclude reactive or real-time adjustment, and the system is demonstrated only on Franka Emika hardware, limiting hardware generalisability.

The pattern across these systems is consistent. Production-validated systems commit to a single coordination mode at design time. Research systems that explore flexibility do so either at the task-planning layer (Fabrica) or at the single-robot level (RoboPilot). The gap resides at the system-integration level.

---

## 6. Joint State and Namespace Integration

The hardware-software integration problem at the state management layer warrants independent treatment, as it is a prerequisite for any dual-arm system operating under a unified planning framework and represents a consistently reinvented engineering challenge.

[Macenski, Foote, Gerkey, Lalancette, and Woodall (2022)](https://doi.org/10.1126/scirobotics.abm6074) describe the ROS2 architecture in *Science Robotics*, documenting namespace isolation as a foundational design principle: each robotic agent operates within a dedicated namespace to prevent identifier conflicts. For dual-arm systems, this means hardware drivers publish joint states under per-robot namespace prefixes using generic joint identifiers, while motion planning infrastructure requires a unified state representation with globally distinct joint names. The transformation between these representations, prefixing on the state aggregation path and stripping on the trajectory dispatch path, is a necessary component of any dual-arm integration and is not provided by the ROS2 or MoveIt2 frameworks.

Two implementation patterns exist in practice. **Passive aggregation** delegates namespace translation to client-side code or post-processing utilities. This approach is minimal in component count but provides no explicit mechanism for timing control, synchronisation guarantees, or consistency monitoring across arm states. **Active aggregation** employs a dedicated middleware node that subscribes to per-arm namespace-scoped topics, applies prefix translation, and publishes a unified state at a controlled frequency. This approach introduces an additional system component but provides explicit control over aggregation timing, a centralised point for state consistency validation, and a defined interface for downstream consumers.

[Lucetti, Lippiello, and Panariello (2026)](https://doi.org/10.1007/978-981-96-8773-2_4) document ROS2 namespace management patterns for multi-robot coordination, identifying active aggregation as emerging best practice for systems requiring planning-layer state consistency. The bidirectionality of the translation problem is non-trivial: the aggregation component must perform forward translation (hardware names to planning names) for joint state publication and reverse translation (planning names to hardware names) for trajectory command dispatch, routing commands to the appropriate per-arm controller.

Community evidence of the gap is explicit: MoveIt2 GitHub issue #2744 (March 2024), "Controlling two Robots simultaneously via MoveIt," was closed as `not_planned`; issue #3037 (October 2024), "Move multiple arms simultaneously," was closed with a recommendation to "explore custom solutions." No canonical solution has been standardised.

---

## 7. Synthesis and Research Gaps

### 7.1 Established Findings

The following findings are supported by empirical evidence of sufficient quality and quantity to be considered established:

- Centralised dual-arm planning is empirically superior to decoupled planning in success rate (99.2% versus approximately 75%) and planning time (1.2–1.8 s versus 2.1–3.2 s) on physical hardware ([Wittmann et al., 2024](https://doi.org/10.1007/s10846-024-02175-3)).
- Planning-time geometric collision avoidance via FCL provides formal safety guarantees that do not depend on training data, generalise across task configurations, and are validated across more than 1,000 deployed systems ([Pan et al., 2012](https://doi.org/10.1109/ICRA.2012.6225337); [Coleman et al., 2014](https://doi.org/10.48550/arXiv.1404.3785)).
- Asynchronous multi-arm execution is implementable within the standard MoveIt2 ecosystem without core framework modification ([Stoop et al., 2024](https://doi.org/10.1109/ICRA57147.2024.10611498)).
- Multiple execution strategies are individually viable and serve qualitatively distinct task requirement profiles; the appropriate strategy is task-dependent rather than universally fixed ([Dreher et al., 2026](https://doi.org/10.48550/arXiv.2603.06538)).
- Runtime strategy selection demonstrably improves system robustness relative to fixed single-mode operation ([Liu et al., 2025](https://doi.org/10.48550/arXiv.2510.00154): 86% versus 0% error recovery).
- Dual-arm coordination delivers commercially significant performance improvements: a 34% cycle time reduction and a positive return on investment within eight months under representative assembly conditions ([Peta et al., 2025](https://doi.org/10.3390/app15062976)).

### 7.2 Unresolved Integration Problem

No published system addresses the integration of these findings into a unified framework. The specific gap is the absence of an open-source architecture that simultaneously provides: (i) centralised dual-arm planning over a unified configuration space; (ii) planning-time geometric collision avoidance with formal safety guarantees; (iii) runtime-selectable coordination modes spanning synchronous, asynchronous, and hybrid execution; (iv) hardware-agnostic deployment on commodity dual-arm platforms without proprietary dependencies; and (v) validated performance on physical hardware with measurable, reproducible metrics.

Each significant contribution in the literature addresses one dimension while leaving others unresolved. [Wittmann et al. (2024)](https://doi.org/10.1007/s10846-024-02175-3) validate the planning architecture but do not address execution strategy. [Stoop et al. (2024)](https://doi.org/10.1109/ICRA57147.2024.10611498) validate asynchronous execution but employ reactive collision avoidance and provide no synchronous or hybrid modes. [Shukla et al. (2025)](https://doi.org/10.3389/frobt.2025.1604506) demonstrate reactive collision avoidance as an execution-layer complement but do not address coordination strategy. [Tian et al. (2025)](https://doi.org/10.48550/arXiv.2506.05168) demonstrate learning-based task decomposition with 80% real-world success but address the task-planning layer exclusively. MoveIt Pro provides a validated planning framework but is closed-source and does not offer native multi-mode execution coordination. ABB YuMi provides production-validated dual-arm coordination within a proprietary, single-mode, hardware-locked architecture.

The integration problem of unifying these individually validated components into a flexible, hardware-agnostic framework with runtime coordination strategy selection constitutes the open research and engineering problem that the existing literature identifies but does not resolve.

---

## References

<a href="https://doi.org/10.1007/s41315-023-00292-0">Abbas, M., Narayan, J., and Dwivedy, S. K. (2023). A systematic review on cooperative dual-arm manipulators: modelling, planning, control, and vision strategies. *International Journal of Intelligent Robotics and Applications*, 7(4), 683–707.</a>

<a href="https://doi.org/10.48550/arXiv.2309.10164">Agarwal, S., Vatnsdal, F., Garcia Camargo, R., Kumar, V., and Alejandro, S. (2023). A scalable multi-robot framework for decentralized and asynchronous perception-action-communication loops. *arXiv preprint arXiv:2309.10164*.</a>

<a href="https://doi.org/10.1016/j.promfg.2020.01.043">Buhl, J. F. et al. (2019). A dual-arm collaborative robot system for the smart factories of the future. *Procedia Manufacturing*, 38, 333–340.</a>

<a href="https://doi.org/10.3390/s24165382">Celik, A. E., Rodriguez, I., Ayestaran, R. G., and Yavuz, S. C. (2024). Decentralized system synchronization among collaborative robots via 5G technology. *Sensors*, 24(16), 5382.</a>

<a href="https://doi.org/10.1007/s10514-018-9726-5">Claes, D. and Tuyls, K. (2018). Multi robot collision avoidance in a shared workspace. *Autonomous Robots*, 42(8), 1749–1770.</a>

<a href="https://doi.org/10.48550/arXiv.1404.3785">Coleman, D., Sucan, I., Chitta, S., and Correll, N. (2014). Reducing the barrier to entry of complex robotic software: a MoveIt! case study. *arXiv preprint arXiv:1404.3785*.</a>

<a href="https://doi.org/10.48550/arXiv.2603.06538">Dreher, C., Dormanns, P., Meixner, A., and Asfour, T. (2026). Unified learning of temporal task structure and action timing for bimanual robot manipulation. *arXiv preprint arXiv:2603.06538*.</a>

<a href="https://doi.org/10.1088/1742-6596/3019/1/012039">Fu, W. et al. (2025). A synchronous control system of dual-arm robot based on digital twin technology. *Journal of Physics: Conference Series*, 3019(1), 012039.</a>

<a href="https://doi.org/10.48550/arXiv.2503.11791">Kaypak, A. U., Wei, S., Krishnamurthy, P., and Khorrami, F. (2025). Safe multi-robotic arm interaction via 3D convex shapes. *arXiv preprint arXiv:2503.11791*.</a>

<a href="https://doi.org/10.1109/ROBOT.2000.844730">Kuffner, J. J. and LaValle, S. M. (2000). RRT-Connect: An efficient approach to single-query path planning. In *Proceedings of the IEEE International Conference on Robotics and Automation (ICRA)*, pp. 995–1001.</a>

<a href="https://doi.org/10.3390/s25226822">Lee, H., Luo, C., and Jung, H. (2025). Multi-agent deep reinforcement learning for collision-free posture control of multi-manipulators in shared workspaces. *Sensors*, 25(22), 6822.</a>

<a href="https://doi.org/10.48550/arXiv.2403.08191">Li, W. et al. (2024). Synchronized dual-arm rearrangement via cooperative mTSP. *arXiv preprint arXiv:2403.08191*.</a>

<a href="https://doi.org/10.48550/arXiv.2510.00154">Liu, X., Fani Sani, M. et al. (2025). RoboPilot: Generalizable dynamic robotic manipulation with dual-thinking modes. *arXiv preprint arXiv:2510.00154*.</a>

<a href="https://doi.org/10.1007/978-981-96-8773-2_4">Lucetti, M., Lippiello, V., and Panariello, D. (2026). ROS2 namespace management patterns for multi-robot coordination. In *Advances in Materials and Manufacturing Technology*. Springer.</a>

<a href="https://doi.org/10.1126/scirobotics.abm6074">Macenski, S., Foote, T., Gerkey, B., Lalancette, C., and Woodall, W. (2022). Robot Operating System 2: Design, architecture, and uses in the wild. *Science Robotics*, 7(66), eabm6074.</a>

<a href="https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=919247">Marvel, J. A., Bostelman, R., and Falco, J. (2014). *Multi-robot assembly strategies and metrics*. National Institute of Standards and Technology.</a>

<a href="https://doi.org/10.1109/TRO.2024.3350183">Montaut, L., Le Lidec, Q., Petrík, V., Sivic, J., and Carpentier, J. (2023). GJK++: Leveraging acceleration methods for faster collision detection. *IEEE Transactions on Robotics*.</a>

<a href="https://doi.org/10.1146/annurev-control-061623-094742">Orthey, A. and Kavraki, L. E. (2024). Sampling-based motion planning: A comparative review. *Annual Review of Control, Robotics, and Autonomous Systems*.</a>

<a href="https://doi.org/10.1109/ICRA.2012.6225337">Pan, J., Chitta, S., and Manocha, D. (2012). FCL: A general purpose library for collision and proximity queries. In *Proceedings of the IEEE International Conference on Robotics and Automation (ICRA)*, pp. 3859–3866.</a>

<a href="https://doi.org/10.1109/MESA61532.2024.10704820">Pantanetti, S., Emiliani, F., Costa, D., Palmieri, G., and Bajrami, A. (2024). From single to dual-arm collaborative robotic assembly: a case study at I-Labs. In *2024 20th IEEE/ASME International Conference on Mechatronic and Embedded Systems and Applications (MESA)*.</a>

<a href="https://doi.org/10.48550/arXiv.2502.16531">Peron, D., Nan Fernandez-Ayala, V., Vlahakis, E. E., and Dimarogonas, D. V. (2025). Efficient coordination and synchronization of multi-robot systems under recurring linear temporal logic. *Autonomous Robots*.</a>

<a href="https://doi.org/10.3390/app15062976">Peta, K., Wiśniewski, M., Kotarski, M., and Ciszak, O. (2025). Comparison of single-arm and dual-arm collaborative robots in precision assembly. *Applied Sciences*, 15(6), 2976.</a>

<a href="https://doi.org/10.1007/s10514-019-09832-9">Shome, R., Solovey, K., Dobson, A., Halperin, D., and Bekris, K. E. (2019). dRRT*: Scalable and informed asymptotically-optimal multi-robot motion planning. *Autonomous Robots*, 44, 443–467.</a>

<a href="https://doi.org/10.3389/frobt.2025.1604506">Shukla, A. et al. (2025). iAPF: An improved artificial potential field framework for asymmetric dual-arm manipulation with real-time inter-arm collision avoidance. *Frontiers in Robotics and AI*, 12.</a>

<a href="https://doi.org/10.3389/frobt.2025.1517887">Silva, G. R. et al. (2025). ROSA: A knowledge-based solution for robot self-adaptation. *Frontiers in Robotics and AI*.</a>

<a href="https://doi.org/10.1016/j.robot.2012.07.005">Smith, C. et al. (2012). Dual arm manipulation: A survey. *Robotics and Autonomous Systems*, 60(10), 1340–1353.</a>

<a href="https://doi.org/10.1109/ICRA57147.2024.10611498">Stoop, P., Ratnayake, T., and Toffetti, G. (2024). A method for multi-robot asynchronous trajectory execution in MoveIt2. In *Proceedings of the IEEE International Conference on Robotics and Automation (ICRA)*.</a>

<a href="https://doi.org/10.1109/MRA.2012.2205651">Sucan, I. A. and Moll, M. (2012). The Open Motion Planning Library. *IEEE Robotics and Automation Magazine*, 19(4), 72–82.</a>

<a href="https://doi.org/10.48550/arXiv.2506.05168">Tian, Y., Jacob, J., Huang, Y. et al. (2025). Fabrica: Dual-arm assembly of general multi-part objects via integrated planning and learning. In *Proceedings of the Conference on Robot Learning (CoRL 2025)*. Best Paper Award.</a>

<a href="https://doi.org/10.1007/s10846-021-01378-2">Verma, J. K. and Ranga, V. (2021). Multi-robot coordination analysis, taxonomy, challenges and future scope. *Journal of Intelligent and Robotic Systems*, 102, Article 10.</a>

<a href="https://doi.org/10.1007/s10846-024-02175-3">Wittmann, J., Ochsenfarth, F., Sonneville, V., and Rixen, D. (2024). Centralized vs. decoupled dual-arm planning taking into account path quality. *Journal of Intelligent and Robotic Systems*, 110, Article 141.</a>

<a href="https://doi.org/10.3390/s23115120">Zhang, H., Jin, H., Ge, M., and Zhao, J. (2023). Real-time kinematically synchronous planning for cooperative manipulation of multi-arms robot using the self-organizing competitive neural network. *Sensors*, 23(11), 5120.</a>

<a href="https://doi.org/10.1007/s11465-026-0873-7">Zhang, Y. and Jia, Y. (2026). Reactive collision-free motion generation for tightly coupled coordinated bimanual manipulation. *Frontiers in Mechanical Engineering*, 21, 100873.</a>

<a href="https://doi.org/10.48550/arXiv.2409.14955">Zhu, X., Xin, Y., Li, S., Liu, H., Xia, C., and Liang, B. (2024). Efficient collision detection framework for enhancing collision-free robot motion. *arXiv preprint arXiv:2409.14955*.</a>
