import { requireMerchantTenant } from "../../lib/tenant";

export async function createOrder() {
  const tenant = requireMerchantTenant();
  return { tenantId: tenant };
}
