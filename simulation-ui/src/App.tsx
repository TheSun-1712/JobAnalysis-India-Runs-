import { useState, useEffect, useRef } from 'react';
import {
  Play,
  Terminal as TerminalIcon,
  Award,
  ShieldAlert,
  Cpu,
  Zap,
  BookOpen,
  ThumbsUp,
  ThumbsDown,
  TrendingUp
} from 'lucide-react';

// ==========================================
// Types and Schemas
// ==========================================
interface Skill {
  name: string;
  duration_months: number;
}

interface Project {
  name: string;
  description: string;
}

interface Candidate {
  candidate_id: string;
  name: string;
  current_title: string;
  years_of_experience: number;
  location: string;
  skills: Skill[];
  projects: Project[];
  prestige_company: boolean;
  job_hopper: boolean;
  expected_salary: number; // in LPA
  git_active: boolean;
  has_research: boolean;
}

interface FeatureVector {
  semantic: number;
  skills: number;
  experience: number;
  project: number;
}

// ==========================================
// Mock Database
// ==========================================
const MOCK_CANDIDATES: Candidate[] = [
  {
    candidate_id: 'CAND_0000001',
    name: 'Alok Kumar',
    current_title: 'Senior Data Engineer',
    years_of_experience: 6.5,
    location: 'Pune, India',
    skills: [
      { name: 'Python', duration_months: 78 },
      { name: 'Spark', duration_months: 60 },
      { name: 'SQL', duration_months: 72 }
    ],
    projects: [
      { name: 'ETL Scaler', description: 'Optimized and scaled legacy data pipelines using Spark.' }
    ],
    prestige_company: false,
    job_hopper: false,
    expected_salary: 22.0,
    git_active: false,
    has_research: false
  },
  {
    candidate_id: 'CAND_0000002',
    name: 'Riya Sen',
    current_title: 'Backend Architect',
    years_of_experience: 7.0,
    location: 'Noida, India',
    skills: [
      { name: 'Python', duration_months: 84 },
      { name: 'AWS', duration_months: 72 },
      { name: 'SQL', duration_months: 60 }
    ],
    projects: [
      { name: 'Cloud Infrastructure', description: 'Designed and deployed scalable cloud backend infrastructure.' }
    ],
    prestige_company: true,
    job_hopper: false,
    expected_salary: 28.0,
    git_active: true,
    has_research: false
  },
  {
    candidate_id: 'CAND_0000003',
    name: 'Fake Candidate',
    current_title: 'Full Stack Engineer',
    years_of_experience: 4.5,
    location: 'Delhi, India',
    skills: [
      { name: 'Next.js 14', duration_months: 72 }, // Honeypot: released in 2023, 6 years exp is impossible in 2026
      { name: 'React', duration_months: 36 }
    ],
    projects: [],
    prestige_company: false,
    job_hopper: false,
    expected_salary: 15.0,
    git_active: false,
    has_research: false
  },
  {
    candidate_id: 'CAND_0000004',
    name: 'Outlier Candidate',
    current_title: 'Architect Advisor',
    years_of_experience: 45.0, // Statistical Outlier
    location: 'Mumbai, India',
    skills: [
      { name: 'Python', duration_months: 12 }
    ],
    projects: [],
    prestige_company: false,
    job_hopper: false,
    expected_salary: 60.0,
    git_active: false,
    has_research: false
  },
  {
    candidate_id: 'CAND_0000005',
    name: 'Aarav Mehta',
    current_title: 'AI Research Scientist',
    years_of_experience: 4.0,
    location: 'Bengaluru, India',
    skills: [
      { name: 'Python', duration_months: 48 },
      { name: 'PyTorch', duration_months: 36 }
    ],
    projects: [
      { name: 'LLM Alignment Research', description: 'Designed and optimized generative text transformers.' }
    ],
    prestige_company: true,
    job_hopper: false,
    expected_salary: 32.0,
    git_active: true,
    has_research: true
  },
  {
    candidate_id: 'CAND_0000006',
    name: 'Neha Sharma',
    current_title: 'Junior Full Stack Engineer',
    years_of_experience: 1.5,
    location: 'Chennai, India',
    skills: [
      { name: 'React', duration_months: 18 },
      { name: 'Python', duration_months: 12 },
      { name: 'Git', duration_months: 18 }
    ],
    projects: [
      { name: 'Personal Website', description: 'Built and deployed personal developer profile portfolio.' }
    ],
    prestige_company: false,
    job_hopper: false,
    expected_salary: 8.5,
    git_active: true,
    has_research: false
  },
  {
    candidate_id: 'CAND_0000007',
    name: 'Vikram Malhotra',
    current_title: 'Senior Developer',
    years_of_experience: 8.0,
    location: 'Gurugram, India',
    skills: [
      { name: 'Python', duration_months: 96 },
      { name: 'Spark', duration_months: 36 },
      { name: 'SQL', duration_months: 80 }
    ],
    projects: [
      { name: 'Data Pipeline', description: 'Implemented data processing pipelines.' }
    ],
    prestige_company: false,
    job_hopper: true, // Penalty: job hopping history
    expected_salary: 26.0,
    git_active: false,
    has_research: false
  },
  {
    candidate_id: 'CAND_0000008',
    name: 'Priya Patel',
    current_title: 'Lead Software Architect',
    years_of_experience: 5.5,
    location: 'Hyderabad, India',
    skills: [
      { name: 'Python', duration_months: 66 },
      { name: 'AWS', duration_months: 48 },
      { name: 'Spark', duration_months: 24 }
    ],
    projects: [
      { name: 'AWS Migration', description: 'Architected and built database clusters migration.' }
    ],
    prestige_company: true, // worked at Google
    job_hopper: false,
    expected_salary: 35.0,
    git_active: true,
    has_research: false
  }
];

// Presets mapping
const JD_PRESETS = {
  data: {
    title: 'Senior Data Engineer',
    text: `Job Title: Senior Data Engineer
Experience: 5-8 years of software development.
Required Skills: python, spark, sql, aws.
Mandate: Own data pipeline structures. Designed and deployed infrastructure.`,
    minExp: 5.0,
    maxExp: 8.0,
    skills: ['python', 'spark', 'sql', 'aws'],
    role: 'Data Engineer',
    seniority: 'Senior'
  },
  web: {
    title: 'Lead Frontend Developer',
    text: `Job Title: Lead Frontend Developer
Experience: 4-7 years of browser UI design.
Required Skills: react, next.js, git, css.
Mandate: Architected scalable interfaces. Built reusable layouts.`,
    minExp: 4.0,
    maxExp: 7.0,
    skills: ['react', 'next.js', 'git', 'css'],
    role: 'Frontend Engineer',
    seniority: 'Lead'
  },
  ai: {
    title: 'AI Research Scientist',
    text: `Job Title: AI Research Scientist
Experience: 3-6 years of ML engineering.
Required Skills: python, pytorch, tensorflow.
Mandate: Published research papers. Designed neural models.`,
    minExp: 3.0,
    maxExp: 6.0,
    skills: ['python', 'pytorch', 'tensorflow'],
    role: 'AI Researcher',
    seniority: 'Research'
  }
};

// Synonym mapping for mock BM25
const SYNONYM_MAP: Record<string, string[]> = {
  python: ['pyspark', 'django', 'fastapi'],
  spark: ['pyspark', 'databricks', 'apache spark'],
  aws: ['amazon web services', 's3', 'lambda', 'cloud'],
  react: ['next.js', 'redux', 'frontend'],
  pytorch: ['tensorflow', 'deep learning', 'ml', 'ai']
};

export default function App() {
  const [presetKey, setPresetKey] = useState<keyof typeof JD_PRESETS>('data');
  const [jdText, setJdText] = useState(JD_PRESETS.data.text);
  const [minExp, setMinExp] = useState(JD_PRESETS.data.minExp);
  const [maxExp, setMaxExp] = useState(JD_PRESETS.data.maxExp);
  const [skills, setSkills] = useState(JD_PRESETS.data.skills);
  const [roleType, setRoleType] = useState(JD_PRESETS.data.role);
  const [seniority, setSeniority] = useState(JD_PRESETS.data.seniority);
  
  const [alpha, setAlpha] = useState(0.5);
  const [mmrEnabled, setMmrEnabled] = useState(true);
  const [banditWeights, setBanditWeights] = useState({
    semantic: 0.2,
    skills: 0.3,
    experience: 0.2,
    project: 0.3
  });
  
  const [isSimulating, setIsSimulating] = useState(false);
  const [consoleLogs, setConsoleLogs] = useState<Array<{ type: string; text: string }>>([
    { type: 'system', text: 'REDOB COGNITIVE PIPELINE CONTROL [V2.6] INITIALIZED.' },
    { type: 'system', text: 'Ready for scanning sequence...' }
  ]);
  
  const [scannedCandidates, setScannedCandidates] = useState<Array<{
    candidate: Candidate;
    status: 'INGESTED' | 'FRAUD' | 'COMPLETE';
    rawScore: number;
    mmrScore: number;
    features: FeatureVector;
    reason: string;
  }>>([]);
  
  const [activeScanCandidate, setActiveScanCandidate] = useState<Candidate | null>(null);
  const [scanStep, setScanStep] = useState<string>('');
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  
  const consoleBodyRef = useRef<HTMLDivElement>(null);
  
  // Custom console logger
  const writeLog = (text: string, type = 'system') => {
    setConsoleLogs(prev => [...prev, { type, text: `[${new Date().toLocaleTimeString()}] ${text}` }]);
  };

  // Scroll console to bottom
  useEffect(() => {
    if (consoleBodyRef.current) {
      consoleBodyRef.current.scrollTop = consoleBodyRef.current.scrollHeight;
    }
  }, [consoleLogs]);

  // Set Preset JD
  const loadPreset = (key: keyof typeof JD_PRESETS) => {
    setPresetKey(key);
    const preset = JD_PRESETS[key];
    setJdText(preset.text);
    setMinExp(preset.minExp);
    setMaxExp(preset.maxExp);
    setSkills(preset.skills);
    setRoleType(preset.role);
    setSeniority(preset.seniority);
    writeLog(`Loaded preset job description: ${preset.title}`, 'info');
  };

  // Run whole pipeline simulation
  const startSimulation = async () => {
    if (isSimulating) return;
    setIsSimulating(true);
    setScannedCandidates([]);
    setSelectedCandidateId(null);
    writeLog(`Starting full ingestion stream of 8 candidate profiles...`, 'info');
    writeLog(`Extracting Job Description parameters...`, 'system');
    writeLog(`Extracted: Seniority=${seniority}, MinExp=${minExp}yr, MaxExp=${maxExp}yr`, 'purple');
    writeLog(`Required stack parsed: ${skills.join(', ')}`, 'purple');

    let currentResults: typeof scannedCandidates = [];

    for (let index = 0; index < MOCK_CANDIDATES.length; index++) {
      const candidate = MOCK_CANDIDATES[index];
      setActiveScanCandidate(candidate);
      setScanStep('Ingesting...');
      writeLog(`Stream reader: Ingesting profile ${candidate.candidate_id} (${candidate.name})`, 'system');
      await delay(1200);

      // Step 2: Honeypot / Fraud check
      setScanStep('Auditing...');
      writeLog(`Security layer: Auditing ${candidate.name} credentials...`, 'system');
      await delay(1000);

      // Honeypot Rules check
      let isFraud = false;
      let fraudReason = '';
      
      // Check Next.js 14 honeypot
      const nextjsSkill = candidate.skills.find(s => s.name.toLowerCase() === 'next.js 14');
      if (nextjsSkill && nextjsSkill.duration_months > 36) {
        isFraud = true;
        fraudReason = `Rule Fraud: Next.js 14 experience (${(nextjsSkill.duration_months / 12).toFixed(1)} years) exceeds real-world launch date of 2023.`;
      }
      
      // Check general experience bounds logic
      candidate.skills.forEach(s => {
        if (s.duration_months / 12 > candidate.years_of_experience + 1) {
          isFraud = true;
          fraudReason = `Rule Fraud: '${s.name}' tenure (${(s.duration_months / 12).toFixed(1)} yrs) exceeds overall career length (${candidate.years_of_experience} yrs).`;
        }
      });

      // Check statistical anomalies
      if (candidate.years_of_experience > 40 && candidate.projects.length === 0) {
        isFraud = true;
        fraudReason = `Statistical Fraud: Profile flagged as outlier anomaly by Isolation Forest model (45.0 yrs exp, 0 projects).`;
      }

      if (isFraud) {
        writeLog(`SECURITY ALERT: ${candidate.name} FLAGGED: ${fraudReason}`, 'danger');
        currentResults.push({
          candidate,
          status: 'FRAUD',
          rawScore: 0,
          mmrScore: 0,
          features: { semantic: 0, skills: 0, experience: 0, project: 0 },
          reason: fraudReason
        });
        setScanStep('Fraud Alert!');
        await delay(1200);
        continue;
      }

      writeLog(`Security check passed for ${candidate.name}. Routing to Scorer.`, 'success');

      // Step 3: Score Candidate
      setScanStep('Scoring Agents...');
      await delay(1000);

      const features = calculateFeatures(candidate);
      const rawScore = 
        features.semantic * banditWeights.semantic +
        features.skills * banditWeights.skills +
        features.experience * banditWeights.experience +
        features.project * banditWeights.project;

      // Construct standout reason
      const standoutReasons: string[] = [];
      if (features.semantic > 0.6) standoutReasons.push('highly relevant keyword BM25 match');
      if (features.skills > 0.7) standoutReasons.push('high intersection with core technology stack');
      if (features.experience > 0.8) standoutReasons.push('optimal experience bracket alignment');
      if (features.project > 0.5) standoutReasons.push('strong verified project action signals');
      if (candidate.prestige_company) standoutReasons.push('prior tenure at top-tier companies');
      if (candidate.git_active) standoutReasons.push('active Github coding history');
      if (candidate.has_research) standoutReasons.push('academic/ML publications and research credentials');
      
      if (candidate.job_hopper) {
        standoutReasons.push('penalized for stability constraints');
      }

      const topStandouts = standoutReasons.slice(0, 3);
      let reasonText = '';
      if (topStandouts.length === 3) {
        reasonText = `Standouts: (1) ${topStandouts[0]}, (2) ${topStandouts[1]}, and (3) ${topStandouts[2]}.`;
      } else if (topStandouts.length === 2) {
        reasonText = `Standouts: (1) ${topStandouts[0]} and (2) ${topStandouts[1]}.`;
      } else if (topStandouts.length === 1) {
        reasonText = `Standouts: (1) ${topStandouts[0]}.`;
      } else {
        reasonText = `Selected based on balanced matching metrics across all 20 agents.`;
      }

      const matchSkillsList = candidate.skills
        .map(s => s.name.toLowerCase())
        .filter(n => skills.includes(n));
      const skillsBody = matchSkillsList.length > 0 
        ? ` Core technical alignment includes: ${matchSkillsList.join(', ')}.`
        : '';
        
      const fullReason = `Recommended for ${candidate.current_title} (${candidate.years_of_experience} yrs). ${reasonText}${skillsBody}`;

      writeLog(`Agent Scorer: Raw score for ${candidate.name} is ${rawScore.toFixed(4)}`, 'purple');
      currentResults.push({
        candidate,
        status: 'COMPLETE',
        rawScore,
        mmrScore: rawScore, // Will be updated in MMR pass
        features,
        reason: fullReason
      });
      
      setScanStep('Completed!');
      await delay(800);
    }

    // Step 4: Apply Jaccard MMR Diversity if active
    setActiveScanCandidate(null);
    setScanStep('');

    if (mmrEnabled) {
      writeLog(`Diversity Pass: Running Maximal Marginal Relevance (MMR) Jaccard filtering...`, 'info');
      await delay(1200);
      currentResults = runMMRFilter(currentResults);
    }

    // Sort valid complete candidates
    currentResults.sort((a, b) => {
      if (a.status === 'FRAUD' && b.status !== 'FRAUD') return 1;
      if (a.status !== 'FRAUD' && b.status === 'FRAUD') return -1;
      if (a.status === 'FRAUD' && b.status === 'FRAUD') return 0;
      // Normal ranking
      return b.mmrScore - a.mmrScore;
    });

    setScannedCandidates(currentResults);
    setIsSimulating(false);
    writeLog(`Pipeline execution finished successfully. Leaderboard generated.`, 'success');
  };

  // Helper Delay
  const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  // Feature Calculators
  const calculateFeatures = (cand: Candidate): FeatureVector => {
    // 1. Semantic (synonym BM25)
    let semCount = 0;
    const candSkillsLower = cand.skills.map(s => s.name.toLowerCase());
    
    skills.forEach(skill => {
      if (candSkillsLower.includes(skill)) {
        semCount += 1.0;
      } else if (SYNONYM_MAP[skill]) {
        // Synonym check
        const hasSynonym = SYNONYM_MAP[skill].some(syn => candSkillsLower.includes(syn));
        if (hasSynonym) semCount += 0.5;
      }
    });
    
    // Scale semantic count
    const semantic = Math.min(1.0, semCount / Math.max(1, skills.length));

    // 2. Exact Skills Match
    const intersection = candSkillsLower.filter(s => skills.includes(s));
    const skillsScore = skills.length > 0 ? intersection.length / skills.length : 1.0;

    // 3. Experience Gaussian
    const mid = (minExp + maxExp) / 2.0;
    const range = maxExp - minExp;
    const sigma = range > 0 ? range / 2.0 : 1.5;
    const diff = cand.years_of_experience - mid;
    const experience = Math.exp(-(diff * diff) / (2 * sigma * sigma));

    // 4. Project action verbs
    let actionWordCount = 0;
    const actionVerbs = ['optimized', 'designed', 'deployed', 'architected', 'implemented', 'built'];
    cand.projects.forEach(p => {
      const descLower = p.description.toLowerCase();
      actionVerbs.forEach(verb => {
        if (descLower.includes(verb)) actionWordCount++;
      });
    });
    const project = Math.min(1.0, actionWordCount / 2.0);

    return { semantic, skills: skillsScore, experience, project };
  };

  // Jaccard similarity between two lists
  const getJaccardSimilarity = (listA: string[], listB: string[]): number => {
    const setA = new Set(listA);
    const setB = new Set(listB);
    const union = new Set([...setA, ...setB]);
    const intersection = listA.filter(x => setB.has(x));
    return union.size > 0 ? intersection.length / union.size : 0.0;
  };

  // MMR re-ranking algorithm
  const runMMRFilter = (results: typeof scannedCandidates) => {
    const lambda = 0.7; // weighting parameter
    const valid = results.filter(r => r.status === 'COMPLETE');
    const fraud = results.filter(r => r.status === 'FRAUD');

    if (valid.length <= 1) return results;

    const selected: typeof valid = [];
    const remaining = [...valid];

    // Select the highest scorer first
    remaining.sort((a, b) => b.rawScore - a.rawScore);
    selected.push(remaining.shift()!);

    while (remaining.length > 0) {
      let bestMMRScore = -Infinity;
      let bestIndex = -1;

      for (let i = 0; i < remaining.length; i++) {
        const cand = remaining[i];
        
        // Calculate max similarity with already selected candidates
        let maxSimilarity = 0;
        selected.forEach(sel => {
          const sim = getJaccardSimilarity(
            cand.candidate.skills.map(s => s.name.toLowerCase()),
            sel.candidate.skills.map(s => s.name.toLowerCase())
          );
          if (sim > maxSimilarity) maxSimilarity = sim;
        });

        // MMR Score formula
        const mmr = lambda * cand.rawScore - (1 - lambda) * maxSimilarity;
        if (mmr > bestMMRScore) {
          bestMMRScore = mmr;
          bestIndex = i;
        }
      }

      if (bestIndex !== -1) {
        const item = remaining.splice(bestIndex, 1)[0];
        item.mmrScore = bestMMRScore; // Apply the penalized MMR score
        selected.push(item);
      } else {
        break;
      }
    }

    return [...selected, ...fraud];
  };

  // Bandit Recruiter Feedback Loop Update (LinUCB mock update)
  const handleRecruiterFeedback = (candidateId: string, reward: number) => {
    const target = scannedCandidates.find(c => c.candidate.candidate_id === candidateId);
    if (!target) return;

    writeLog(`Feedback Loop: Recruiter feedback received for ${target.candidate.name} (Reward=${reward > 0 ? '+1.0' : '0.0'})`, 'info');

    // Drift current weights toward candidate feature vector coordinates
    const features = target.features;
    const step = 0.08; // learning step size

    const newWeights = { ...banditWeights };
    if (reward > 0) {
      newWeights.semantic = Math.max(0.05, Math.min(0.6, newWeights.semantic + (features.semantic - newWeights.semantic) * step));
      newWeights.skills = Math.max(0.05, Math.min(0.6, newWeights.skills + (features.skills - newWeights.skills) * step));
      newWeights.experience = Math.max(0.05, Math.min(0.6, newWeights.experience + (features.experience - newWeights.experience) * step));
      newWeights.project = Math.max(0.05, Math.min(0.6, newWeights.project + (features.project - newWeights.project) * step));
    } else {
      newWeights.semantic = Math.max(0.05, Math.min(0.6, newWeights.semantic - (features.semantic - newWeights.semantic) * step * 0.5));
      newWeights.skills = Math.max(0.05, Math.min(0.6, newWeights.skills - (features.skills - newWeights.skills) * step * 0.5));
      newWeights.experience = Math.max(0.05, Math.min(0.6, newWeights.experience - (features.experience - newWeights.experience) * step * 0.5));
      newWeights.project = Math.max(0.05, Math.min(0.6, newWeights.project - (features.project - newWeights.project) * step * 0.5));
    }

    // Re-normalize weights to sum to 1.0 roughly
    const sum = newWeights.semantic + newWeights.skills + newWeights.experience + newWeights.project;
    newWeights.semantic = parseFloat((newWeights.semantic / sum).toFixed(4));
    newWeights.skills = parseFloat((newWeights.skills / sum).toFixed(4));
    newWeights.experience = parseFloat((newWeights.experience / sum).toFixed(4));
    newWeights.project = parseFloat((newWeights.project / sum).toFixed(4));

    setBanditWeights(newWeights);
    
    // Dynamically recalculate scores
    const updatedCandidates = scannedCandidates.map(c => {
      if (c.status === 'FRAUD') return c;
      const rawScore = 
        c.features.semantic * newWeights.semantic +
        c.features.skills * newWeights.skills +
        c.features.experience * newWeights.experience +
        c.features.project * newWeights.project;
      return { ...c, rawScore, mmrScore: rawScore };
    });

    const finalizedList = mmrEnabled ? runMMRFilter(updatedCandidates) : updatedCandidates;
    
    finalizedList.sort((a, b) => {
      if (a.status === 'FRAUD' && b.status !== 'FRAUD') return 1;
      if (a.status !== 'FRAUD' && b.status === 'FRAUD') return -1;
      return b.mmrScore - a.mmrScore;
    });

    setScannedCandidates(finalizedList);
    writeLog(`Bandit Theta recalculated. New weights: Semantic=${newWeights.semantic.toFixed(2)}, Skills=${newWeights.skills.toFixed(2)}, Exp=${newWeights.experience.toFixed(2)}, Proj=${newWeights.project.toFixed(2)}`, 'purple');
  };

  const selectedCandidateData = scannedCandidates.find(c => c.candidate.candidate_id === selectedCandidateId);

  return (
    <div className="app-container">
      {/* Header Panel */}
      <header className="header-bar">
        <div className="header-title-section">
          <h1>Redrob Cognitive ATS Simulator</h1>
          <p>Multi-Agent Reinforcement Learning Engine</p>
        </div>
        <div className="status-badges">
          <div className="badge cyan">Role: {roleType}</div>
          <div className="badge cyan">
            <span className="pulse-dot"></span>
            System Online
          </div>
          <div className="badge purple">20 Agents Loaded</div>
          <div className="badge green">LinUCB active</div>
          <div className="badge amber">Database cached</div>
        </div>
      </header>

      {/* Grid Dashboard */}
      <div className="dashboard-grid">
        
        {/* COLUMN 1: Inputs & Configs */}
        <div className="column">
          <div className="tech-card active-border" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div className="column-header">
              <span>Job Description Input</span>
              <BookOpen size={14} className="glow-cyan" />
            </div>

            {/* Presets */}
            <div className="presets-grid">
              <button
                className={`preset-btn ${presetKey === 'data' ? 'active' : ''}`}
                onClick={() => loadPreset('data')}
              >
                Data Eng
              </button>
              <button
                className={`preset-btn ${presetKey === 'web' ? 'active' : ''}`}
                onClick={() => loadPreset('web')}
              >
                Frontend
              </button>
              <button
                className={`preset-btn ${presetKey === 'ai' ? 'active' : ''}`}
                onClick={() => loadPreset('ai')}
              >
                AI Sci
              </button>
            </div>

            {/* JD Editor */}
            <div className="jd-editor-container">
              <textarea
                className="jd-textarea"
                value={jdText}
                onChange={e => setJdText(e.target.value)}
              />
            </div>

            {/* Simulator config sliders */}
            <div className="config-group">
              <div className="config-item">
                <div className="config-label-row">
                  <span>Experience Target Bounds</span>
                  <span>{minExp.toFixed(1)} - {maxExp.toFixed(1)} Years</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="15"
                  step="0.5"
                  className="config-slider"
                  value={minExp}
                  onChange={e => setMinExp(parseFloat(e.target.value))}
                />
              </div>

              <div className="config-item">
                <div
                  className={`toggle-container ${mmrEnabled ? 'active' : ''}`}
                  onClick={() => setMmrEnabled(!mmrEnabled)}
                >
                  <div className="config-label-row" style={{ flexDirection: 'column', gap: '2px' }}>
                    <span>MMR Diversity Filter</span>
                    <span style={{ fontSize: '8px', color: '#5b6875', textTransform: 'lowercase' }}>
                      re-rank by skill variety
                    </span>
                  </div>
                  <div className="toggle-switch"></div>
                </div>
              </div>

              <div className="config-item">
                <div className="config-label-row">
                  <span>Bandit Exploration Scale (&alpha;)</span>
                  <span>{alpha.toFixed(2)}</span>
                </div>
                <input
                  type="range"
                  min="0.1"
                  max="1.5"
                  step="0.05"
                  className="config-slider"
                  value={alpha}
                  onChange={e => setAlpha(parseFloat(e.target.value))}
                />
              </div>
            </div>

            {/* Run Action controls */}
            <div className="action-buttons">
              <button
                className="primary-btn"
                disabled={isSimulating}
                onClick={startSimulation}
              >
                <Play size={14} fill="currentColor" />
                Run Ingestion Stream
              </button>
              <button
                className="secondary-btn"
                onClick={() => {
                  setScannedCandidates([]);
                  setSelectedCandidateId(null);
                  setConsoleLogs([
                    { type: 'system', text: 'REDOB COGNITIVE PIPELINE CONTROL RESET.' }
                  ]);
                }}
              >
                Reset Simulator
              </button>
            </div>
          </div>
        </div>

        {/* COLUMN 2: Monitor & Ingestion Scanner */}
        <div className="column">
          {/* Scanner view */}
          <div className="tech-card active-border scanner-panel">
            <div className="column-header">
              <span>Ingestion Stream Scanning View</span>
              <Cpu size={14} className="glow-cyan" />
            </div>
            <div className="scanner-viewport">
              {isSimulating && <div className="scanner-line"></div>}

              {activeScanCandidate ? (
                <div className={`scanner-candidate-card`}>
                  <div className="scanner-header">
                    <span className="scan-title">{activeScanCandidate.name}</span>
                    <span className="scan-status-text">{scanStep}</span>
                  </div>
                  <div className="scanner-details">
                    <div className="scan-detail-row">
                      <span>ID:</span>
                      <span>{activeScanCandidate.candidate_id}</span>
                    </div>
                    <div className="scan-detail-row">
                      <span>Title:</span>
                      <span>{activeScanCandidate.current_title}</span>
                    </div>
                    <div className="scan-detail-row">
                      <span>Experience:</span>
                      <span>{activeScanCandidate.years_of_experience} Years</span>
                    </div>
                    <div className="scan-detail-row">
                      <span>Skills Matrix:</span>
                      <span style={{ fontSize: '8px' }}>
                        {activeScanCandidate.skills.map(s => s.name).join(', ')}
                      </span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="no-selection">
                  Scanner Idle - Awaiting Stream Ingestion
                </div>
              )}
            </div>
          </div>

          {/* Console logs */}
          <div className="tech-card active-border console-panel" style={{ flex: 1, minHeight: 0 }}>
            <div className="column-header">
              <span>Simulator Console Log</span>
              <TerminalIcon size={14} className="glow-cyan" />
            </div>
            <div className="console-body" ref={consoleBodyRef}>
              {consoleLogs.map((log, index) => (
                <div key={index} className={`console-line ${log.type}`}>
                  {log.text}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* COLUMN 3: Leaderboard & Bandit charts */}
        <div className="column">
          {/* Bandit Weights chart */}
          <div className="tech-card active-border bandit-panel">
            <div className="column-header">
              <span>RL Contextual Bandit Weight Estimation</span>
              <TrendingUp size={14} className="glow-purple" />
            </div>
            <div className="bandit-bars">
              <div className="bandit-bar-item">
                <div className="bandit-bar-label">
                  <span>Semantic BM25 Weight</span>
                  <span>{(banditWeights.semantic * 100).toFixed(1)}%</span>
                </div>
                <div className="bandit-bar-track">
                  <div className="bandit-bar-fill" style={{ width: `${banditWeights.semantic * 100}%` }}></div>
                </div>
              </div>
              <div className="bandit-bar-item">
                <div className="bandit-bar-label">
                  <span>Exact Skills Match Weight</span>
                  <span>{(banditWeights.skills * 100).toFixed(1)}%</span>
                </div>
                <div className="bandit-bar-track">
                  <div className="bandit-bar-fill" style={{ width: `${banditWeights.skills * 100}%` }}></div>
                </div>
              </div>
              <div className="bandit-bar-item">
                <div className="bandit-bar-label">
                  <span>Gaussian Experience Weight</span>
                  <span>{(banditWeights.experience * 100).toFixed(1)}%</span>
                </div>
                <div className="bandit-bar-track">
                  <div className="bandit-bar-fill" style={{ width: `${banditWeights.experience * 100}%` }}></div>
                </div>
              </div>
              <div className="bandit-bar-item">
                <div className="bandit-bar-label">
                  <span>Project Signal Weight</span>
                  <span>{(banditWeights.project * 100).toFixed(1)}%</span>
                </div>
                <div className="bandit-bar-track">
                  <div className="bandit-bar-fill" style={{ width: `${banditWeights.project * 100}%` }}></div>
                </div>
              </div>
            </div>
          </div>

          {/* Ranking Leaderboard */}
          <div className="tech-card active-border leaderboard-panel">
            <div className="column-header">
              <span>Ranked Shortlist Leaderboard</span>
              <Award size={14} className="glow-green" />
            </div>
            <div className="leaderboard-list">
              {scannedCandidates.length > 0 ? (
                scannedCandidates.map((c, i) => (
                  <div
                    key={c.candidate.candidate_id}
                    className={`candidate-row ${selectedCandidateId === c.candidate.candidate_id ? 'selected' : ''} ${c.status === 'FRAUD' ? 'fraud' : ''}`}
                    onClick={() => setSelectedCandidateId(c.candidate.candidate_id)}
                  >
                    <div className="candidate-rank-badge">
                      {c.status === 'FRAUD' ? '!' : i + 1}
                    </div>
                    <div className="candidate-info">
                      <div className="candidate-name-row">
                        <span className="cand-name">{c.candidate.name}</span>
                        <span className="cand-score">
                          {c.status === 'FRAUD' ? 'AUDITED' : c.mmrScore.toFixed(4)}
                        </span>
                      </div>
                      <span className="cand-meta">
                        {c.candidate.current_title} ({c.candidate.years_of_experience} yrs) - {c.candidate.location}
                      </span>
                    </div>

                    {c.status === 'COMPLETE' && (
                      <div className="feedback-actions" onClick={e => e.stopPropagation()}>
                        <button
                          className="feedback-btn shortlist"
                          title="Shortlist Candidate (Bandit Feedback +1.0)"
                          onClick={() => handleRecruiterFeedback(c.candidate.candidate_id, 1.0)}
                        >
                          <ThumbsUp size={10} />
                        </button>
                        <button
                          className="feedback-btn decline"
                          title="Reject Candidate (Bandit Feedback -0.5)"
                          onClick={() => handleRecruiterFeedback(c.candidate.candidate_id, 0.0)}
                        >
                          <ThumbsDown size={10} />
                        </button>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="no-selection">
                  Leaderboard Empty - Start Scanning Sequence
                </div>
              )}
            </div>
          </div>
        </div>

      </div>

      {/* FOOTER DIAGNOSTICS OF SELECTED CANDIDATE */}
      <footer className="tech-card active-border diagnostics-panel" style={{ height: '240px' }}>
        <div className="column-header">
          <span>Candidate Diagnostic Agent Logs</span>
          <Zap size={14} className="glow-purple" />
        </div>
        {selectedCandidateData ? (
          <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
            <div className="diagnostics-header">
              <span className="diag-name">{selectedCandidateData.candidate.name} Diagnostics</span>
              <p className="diag-desc">{selectedCandidateData.reason}</p>
            </div>
            <div className="diagnostics-body">
              {selectedCandidateData.status === 'FRAUD' ? (
                <div style={{ color: 'var(--neon-red)', fontSize: '12px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px', padding: '12px' }}>
                  <ShieldAlert size={20} />
                  SECURITY ALERT: PROFILE EXCLUDED FROM SCORING POOL DUE TO DETECTED ANOMALOUS FRAUD SIGNALS.
                </div>
              ) : (
                <div className="agents-grid">
                  <div className="agent-grid-item">
                    <span className="agent-item-name">Semantic BM25 Agent</span>
                    <div className="agent-item-score-row">
                      <span className="agent-item-score primary">
                        {selectedCandidateData.features.semantic.toFixed(4)}
                      </span>
                      <span className="agent-item-rank">Weight: {(banditWeights.semantic * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                  <div className="agent-grid-item">
                    <span className="agent-item-name">Exact Skills Agent</span>
                    <div className="agent-item-score-row">
                      <span className="agent-item-score primary">
                        {selectedCandidateData.features.skills.toFixed(4)}
                      </span>
                      <span className="agent-item-rank">Weight: {(banditWeights.skills * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                  <div className="agent-grid-item">
                    <span className="agent-item-name">Gaussian Exp Agent</span>
                    <div className="agent-item-score-row">
                      <span className="agent-item-score primary">
                        {selectedCandidateData.features.experience.toFixed(4)}
                      </span>
                      <span className="agent-item-rank">Weight: {(banditWeights.experience * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                  <div className="agent-grid-item">
                    <span className="agent-item-name">Project Signals Agent</span>
                    <div className="agent-item-score-row">
                      <span className="agent-item-score primary">
                        {selectedCandidateData.features.project.toFixed(4)}
                      </span>
                      <span className="agent-item-rank">Weight: {(banditWeights.project * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                  <div className="agent-grid-item">
                    <span className="agent-item-name">Company Prestige Agent</span>
                    <div className="agent-item-score-row">
                      <span className="agent-item-score secondary">
                        {selectedCandidateData.candidate.prestige_company ? '1.0000' : '0.0000'}
                      </span>
                      <span className="agent-item-rank">Multiplier Tier-1</span>
                    </div>
                  </div>
                  <div className="agent-grid-item">
                    <span className="agent-item-name">Job Stability Agent</span>
                    <div className="agent-item-score-row">
                      <span className="agent-item-score secondary">
                        {selectedCandidateData.candidate.job_hopper ? '0.2000' : '1.0000'}
                      </span>
                      <span className="agent-item-rank">
                        {selectedCandidateData.candidate.job_hopper ? 'Penalized' : 'Stable'}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="no-selection">
            Select a candidate from the shortlist to view specific agent scores.
          </div>
        )}
      </footer>
    </div>
  );
}
