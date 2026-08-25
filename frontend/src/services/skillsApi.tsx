// Install a skill
export async function installSkill(skillName: string): Promise<{ok: boolean, skill_name: string}> {
  const response = await fetch('/api/skills/install', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ skill_name: skillName }),
  });
  
  if (!response.ok) {
    throw new Error('Failed to install skill');
  }
  
  return response.json();
}

// Uninstall a skill
export async function uninstallSkill(skillName: string): Promise<{ok: boolean, skill_name: string}> {
  const response = await fetch(`/api/skills/uninstall?skill_name=${skillName}`, {
    method: 'DELETE',
  });
  
  if (!response.ok) {
    throw new Error('Failed to uninstall skill');
  }
  
  return response.json();
}

// Get available skills with installation status
export async function getAvailableSkills(): Promise<{available_skills: Array<{skill_name: string, installed: boolean, tools_count: number}>}> {
  const response = await fetch('/api/skills/available');
  
  if (!response.ok) {
    throw new Error('Failed to get available skills');
  }
  
  return response.json();
}