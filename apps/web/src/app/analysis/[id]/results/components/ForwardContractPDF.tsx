import { Document, Page, StyleSheet, Text, View } from "@react-pdf/renderer";

import { BankInstructionDraft } from "@/lib/types";

interface ForwardContractPDFProps {
  draft: BankInstructionDraft;
}

const styles = StyleSheet.create({
  page: {
    padding: 42,
    fontSize: 10,
    fontFamily: "Helvetica",
    color: "#111827",
  },
  brand: {
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 6,
  },
  title: {
    fontSize: 14,
    fontWeight: "bold",
    marginBottom: 18,
    paddingBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#111827",
  },
  section: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 11,
    fontWeight: "bold",
    marginBottom: 8,
  },
  row: {
    flexDirection: "row",
    borderBottomWidth: 1,
    borderBottomColor: "#E5E7EB",
    paddingVertical: 6,
  },
  label: {
    width: "38%",
    color: "#4B5563",
  },
  value: {
    width: "62%",
    fontWeight: "bold",
  },
  paragraph: {
    lineHeight: 1.5,
    marginBottom: 8,
  },
  signature: {
    marginTop: 42,
    width: "55%",
    borderTopWidth: 1,
    borderTopColor: "#111827",
    paddingTop: 8,
  },
});

export function ForwardContractPDF({ draft }: ForwardContractPDFProps) {
  return (
    <Document>
      <Page size="A4" style={styles.page}>
        <Text style={styles.brand}>LINTASNIAGA</Text>
        <Text style={styles.title}>{draft.title}</Text>

        <View style={styles.section}>
          <Text style={styles.paragraph}>Date: {new Date(draft.generated_at).toLocaleDateString()}</Text>
          <Text style={styles.paragraph}>To: Relationship Manager, Maybank / CIMB Corporate Banking</Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Forward Contract Request</Text>
          <View style={styles.row}>
            <Text style={styles.label}>SME Name</Text>
            <Text style={styles.value}>{draft.sme_name}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Supplier</Text>
            <Text style={styles.value}>{draft.supplier_name}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Target Currency</Text>
            <Text style={styles.value}>{draft.target_currency}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Notional Amount</Text>
            <Text style={styles.value}>
              {draft.target_currency} {draft.amount.toLocaleString(undefined, { maximumFractionDigits: 2 })}
            </Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Tenor</Text>
            <Text style={styles.value}>{draft.tenor_days} days</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Requested Strike Reference</Text>
            <Text style={styles.value}>{draft.requested_strike_rate.toFixed(6)}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Hedge Ratio</Text>
            <Text style={styles.value}>{draft.hedge_ratio.toFixed(0)}%</Text>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Business Justification</Text>
          <Text style={styles.paragraph}>{draft.business_justification}</Text>
          <Text style={styles.sectionTitle}>Risk Rationale</Text>
          <Text style={styles.paragraph}>{draft.risk_rationale}</Text>
        </View>

        <Text style={styles.paragraph}>
          We request your assistance to quote and execute the above forward exchange contract subject to prevailing
          bank documentation, credit lines, and compliance checks.
        </Text>

        <View style={styles.signature}>
          <Text>Authorised Signatory</Text>
        </View>
      </Page>
    </Document>
  );
}
