import type { GraphNode, GraphEdge, RingRow } from './types';

export const mockNodes: GraphNode[] = [
  { id: 'n1', x: 60, y: 80, color: 'normal' },
  { id: 'n2', x: 160, y: 60, color: 'high', ring: 'RING_001', score: 87.5, inTx: 12, outTx: 8, totalAmount: 250000, activeDays: 28, activeTxAmount: 18000 },
  { id: 'n3', x: 240, y: 110, color: 'normal' },
  { id: 'n4', x: 120, y: 160, color: 'medium_high', ring: 'RING_002', score: 61.4, inTx: 5, outTx: 15, totalAmount: 89000, activeDays: 14, activeTxAmount: 6400 },
  { id: 'n5', x: 310, y: 70, color: 'normal' },
  { id: 'n6', x: 390, y: 90, color: 'normal' },
  { id: 'n7', x: 470, y: 60, color: 'high', ring: 'RING_001', score: 72.1, inTx: 9, outTx: 11, totalAmount: 130000, activeDays: 21, activeTxAmount: 9800 },
  { id: 'n8', x: 550, y: 80, color: 'normal' },
  { id: 'n9', x: 620, y: 60, color: 'high' },
  { id: 'n10', x: 690, y: 90, color: 'medium_high', ring: 'RING_003', score: 55.0, inTx: 20, outTx: 3, totalAmount: 44000, activeDays: 7, activeTxAmount: 3200 },
  { id: 'n11', x: 50, y: 230, color: 'high' },
  { id: 'n12', x: 150, y: 260, color: 'critical', ring: 'RING_001', score: 95.3, inTx: 18, outTx: 22, totalAmount: 480000, activeDays: 35, activeTxAmount: 41000 },
  { id: 'n13', x: 240, y: 240, color: 'normal' },
  { id: 'n14', x: 340, y: 260, color: 'critical', ring: 'RING_001', score: 91.0, inTx: 15, outTx: 17, totalAmount: 360000, activeDays: 30, activeTxAmount: 35000 },
  { id: 'n15', x: 440, y: 240, color: 'critical', ring: 'RING_001', score: 88.2, inTx: 11, outTx: 14, totalAmount: 290000, activeDays: 25, activeTxAmount: 22000 },
  { id: 'n16', x: 530, y: 260, color: 'normal' },
  { id: 'n17', x: 620, y: 240, color: 'high' },
  { id: 'n18', x: 700, y: 260, color: 'high', ring: 'RING_002', score: 70.5, inTx: 8, outTx: 10, totalAmount: 120000, activeDays: 18, activeTxAmount: 8500 },
  { id: 'n19', x: 80, y: 350, color: 'medium_high' },
  { id: 'n20', x: 190, y: 370, color: 'high' },
  { id: 'n21', x: 280, y: 340, color: 'high', ring: 'RING_002', score: 68.0, inTx: 7, outTx: 12, totalAmount: 95000, activeDays: 12, activeTxAmount: 7200 },
  { id: 'n22', x: 370, y: 370, color: 'normal' },
  { id: 'n23', x: 460, y: 350, color: 'high', ring: 'RING_002', score: 73.8, inTx: 10, outTx: 9, totalAmount: 145000, activeDays: 20, activeTxAmount: 11000 },
  { id: 'n24', x: 560, y: 360, color: 'normal' },
  { id: 'n25', x: 650, y: 350, color: 'high' },
  { id: 'n26', x: 730, y: 370, color: 'medium_high' },
  { id: 'n27', x: 110, y: 460, color: 'medium_high', ring: 'RING_003', score: 58.9, inTx: 6, outTx: 8, totalAmount: 67000, activeDays: 9, activeTxAmount: 4800 },
  { id: 'n28', x: 210, y: 450, color: 'normal' },
  { id: 'n29', x: 300, y: 470, color: 'medium_high', ring: 'RING_003', score: 62.1, inTx: 8, outTx: 7, totalAmount: 78000, activeDays: 11, activeTxAmount: 5600 },
  { id: 'n30', x: 400, y: 450, color: 'normal' },
  { id: 'n31', x: 490, y: 470, color: 'medium_high' },
  { id: 'n32', x: 590, y: 450, color: 'high' },
  { id: 'n33', x: 680, y: 470, color: 'medium_high', ring: 'RING_003', score: 60.3, inTx: 9, outTx: 6, totalAmount: 82000, activeDays: 13, activeTxAmount: 6100 },
  { id: 'n34', x: 750, y: 450, color: 'normal' },
];

export const mockEdges: GraphEdge[] = [
  { from: 'n1', to: 'n3' },
  { from: 'n3', to: 'n4' },
  { from: 'n12', to: 'n14' },
  { from: 'n14', to: 'n15' },
  { from: 'n21', to: 'n23' },
  { from: 'n23', to: 'n29' },
];

export const mockRings: RingRow[] = [
  { ringId: 'RING_001', patternType: 'Cycle + Smurfing', members: 5, riskScore: 95.3, accounts: 'ACC_001, ACC_002, ACC_003, ACC_004, ACC_005' },
  { ringId: 'RING_002', patternType: 'Shell Network', members: 4, riskScore: 72.1, accounts: 'ACC_010, ACC_011, ACC_012, ACC_013' },
  { ringId: 'RING_003', patternType: 'Fan-Out (Smurfing)', members: 12, riskScore: 61.4, accounts: 'ACC_020, ACC_021, ... +10 more' },
];

export const jsonOutputPlaceholder = `{
  "suspicious_accounts": [
    {
      "account_id": "ACC_00123",
      "suspicion_score": 87.5,
      "detected_patterns": ["cycle_length_3", "high_velocity"],
      "ring_id": "RING_001"
    }
  ],
  "fraud_rings": [...],
  "summary": {
    "total_accounts_analyzed": 500,
    "suspicious_accounts_flagged": 15,
    "fraud_rings_detected": 4,
    "processing_time_seconds": 2.3
  }
}`;
