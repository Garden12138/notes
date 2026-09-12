export interface ArchitectureLayer {
  name: string;
  technology: string;
  responsibilities: string[];
}

export interface AgentRole {
  name: string;
  display_name: string;
  responsibility: string;
  expected_inputs: string[];
  expected_outputs: string[];
  external_capabilities: string[];
}

export interface ExternalIntegration {
  purpose: string;
  configured: boolean;
}

export interface ArchitectureSnapshot {
  project: string;
  scope: string;
  layers: ArchitectureLayer[];
  agents: AgentRole[];
  external_integrations: Record<string, ExternalIntegration>;
  data_flow: string[];
  implemented_capabilities: string[];
  deferred_capabilities: string[];
}

