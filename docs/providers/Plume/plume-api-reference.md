# Plume Cloud API Reference

Generated: 2026-08-13T20:26:18.956Z  
Source: gamma.noc.plume.com/explorer

This document covers three API groups: Customer, Reports, and LTE. Each endpoint lists its HTTP method, path, required parameters, all parameters, possible response codes, and an example response body where available.

---
## Customer API (v1.164.0)
Base URL: `piranha-gamma.prod.us-west-2.aws.plumenet.io/api`  
Customer APIs for NOC, IOS, Android, QA scripts

### Group
Manage groups and resources assigned to groups.

Partner APIs are almost identical in their usage and are located under the /api/partners/* prefix. Partner APIs are preferred for most use cases, but there are specific scenarios where Groups APIs may be used for certain customers.

The APIs can only be called by system users, be it administrators or other roles. The APIs are not accessible by regular customers.

#### `PUT` `/Groups/{id}/customers/rel/{fk}`
*Assign customer to group*

Assign customer to a group. Customer can be assigned to multiple groups at the same time.

Assigning customer to a group will allow `group admins` and `group support technicians` to manage this customer and view its configs.
If the group is linked to a `cohort` config, assigning customer to this group will also apply those configs to customer's locations.

operationId: `Group.prototype.__link__customers__put_Groups_{id}_customers_rel_{fk}`

**Required to call:** `id` (path), `fk` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Group id |
| `fk` | path | string | **REQUIRED** | Customer id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Customer or group not found; `500` Unhandled API error

#### `DELETE` `/Groups/{id}/customers/rel/{fk}`
*Unassign customer from group*

Unassign customer from a group.

Unassigning customer from a group may result in `group admins` and `group support technicians` loosing access to view/administer the customer.
If the group is linked to a `cohort` config, unassigning customer from the group will also undo cohort configs applied to customer's locations.

operationId: `Group.prototype.__unlink__customers__delete_Groups_{id}_customers_rel_{fk}`

**Required to call:** `id` (path), `fk` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Group id |
| `fk` | path | string | **REQUIRED** | Customer id |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `404` Customer or group not found; `500` Unhandled API error

#### `GET` `/Groups/{id}/customers`
*Get customers belonging to group*

Return all customers belonging to a group.

By default it returns the first 500 customers. In order to paginate through all, you need to utilize the `filter` query parameter.

operationId: `Group.prototype.__get__customers__get_Groups_{id}_customers`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Group id |
| `filter` | query | string | optional | Filter defining fields, where, include, order, offset, and limit - must be a JSON-encoded string (`{"where":{"something":"value"}}`).  See https://loopback.io/doc/en/lb3/Querying-data.html#using-stringified-json-in-rest-queries for more details. |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `404` Group not found; `500` Unhandled API error

#### `GET` `/Groups/{id}`
*Find group by id*

Find a single group based on its unique identifier.

operationId: `Group.findById__get_Groups_{id}`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Group id |
| `filter` | query | string | optional | Filter defining fields, where, include, order, offset, and limit - must be a JSON-encoded string (`{"where":{"something":"value"}}`).  See https://loopback.io/doc/en/lb3/Querying-data.html#using-stringified-json-in-rest-queries for more details. |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `404` Group not found; `500` Unhandled API error

#### `PUT` `/Groups/{id}`
*Update group*

Update group properties.

All body properties are optional, the API will also succeed if no body parameters are sent, in that case it behaves the same as `GET /api/groups/:id`.

operationId: `Group.prototype.patchAttributes__put_Groups_id_`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Group id |
| `data` | body | Group | optional |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `403` Forbidden; `404` Group not found; `500` Unhandled API error

#### `DELETE` `/Groups/{id}`
*Delete group*

Remove group and unassign customers belonging to said group.

Calling this API with an invalid group id, will also return a 200 response. The `count` property should be 0 in that case.

operationId: `Group.prototype.delete`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Group id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `423` Can't delete. Please remove partnerId in the Inventory first; `500` Unhandled API error

#### `PATCH` `/Groups/{id}`
*Update group*

Update group properties.

All body properties are optional, the API will also succeed if no body parameters are sent, in that case it behaves the same as `GET /api/groups/:id`.

operationId: `Group.prototype.patchAttributes__patch_Groups_id_`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Group id |
| `data` | body | Group | optional |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `403` Forbidden; `404` Group not found; `500` Unhandled API error

#### `GET` `/Groups`
*Get groups*

Get all groups.

By default it returns the first 500 groups. In order to paginate through all, you need to utilize the `filter` query parameter.

operationId: `Group.find__get_Groups`

**Required to call:** none

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `filter` | query | string | optional | Filter defining fields, where, include, order, offset, and limit - must be a JSON-encoded string (`{"where":{"something":"value"}}`).  See https://loopback.io/doc/en/lb3/Querying-data.html#using-stringified-json-in-rest-queries for more details. |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `404` Group not found; `500` Unhandled API error

#### `POST` `/Groups`
*Create group*

Create new group.

Both name and description cannot contain &lt; or &gt; characters.

operationId: `Group.customCreate`

**Required to call:** none

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `data` | body | GroupCustomCreate | optional |  |

**Possible responses:** `200` Request was successful; `400` Missing required argument; `401` Authorization failed; `403` Forbidden; `422` Invalid request; `500` Unhandled API error

#### `GET` `/Groups/count`
*Count groups*

Count all groups.

By default it returns the count of all groups. You can use the `where` query parameter to narrow down the count.

operationId: `Group.count__get_Groups_count`

**Required to call:** none

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `where` | query | string | optional | Criteria to match groups. For example: `{"name": "test-name"}` |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `500` Unhandled API error

#### `GET` `/Groups/customers/search/{keyword}`
*Find customers in groups*

Find customers amongst groups the API caller is a `group admin` or `group support technician` in.

The API returns a maximum of 10 results. Please use `?exactMatch=true&startsWith=true` whenever possible as it speeds up the API response.
If no results matched the keyword then the API will return an empty array.

This API is deprecated in favour of using the `GET /api/partners/customers/search/:keyword`.

operationId: `Group.findCustomers`

**Required to call:** `keyword` (path), `field` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `keyword` | path | string | **REQUIRED** | Search term |
| `field` | query | string | **REQUIRED** | Search field |
| `exactMatch` | query | boolean | optional | Only look for exact matches to keyword |
| `startsWith` | query | boolean | optional | Only find customers where field starts with keyword |

**Possible responses:** `200` Request was successful; `400` Missing required argument; `401` Authorization failed; `422` Invalid request; `500` Unhandled API error

#### `GET` `/Groups/customers/{keyword}`
*Find customers in groups*

Find customers amongst groups the API caller is a `group admin` or `group support technician` in.

The API returns a maximum of 10 results.
If no results matched the keyword then the API will return an empty array.

This API is deprecated in favour of using the `GET /api/partners/customers/:keyword`.

operationId: `Group.getCustomers`

**Required to call:** `keyword` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `keyword` | path | string | **REQUIRED** | Search term. Could be email, name, id, even a partial match. |

**Possible responses:** `200` Request was successful; `400` Missing required argument; `401` Authorization failed; `403` Forbidden; `500` Unhandled API error

#### `GET` `/Groups/locations/{keyword}`
*Find location in groups*

Find location amongst groups the API caller is a `group admin` or `group support technician` in.
Finds a location matching either the locationId or serviceId.
This API id being deprecated in favour of `GET /api/partners/locations/:keyword`.

operationId: `Group.getLocations`

**Required to call:** `keyword` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `keyword` | path | string | **REQUIRED** | Search term. Could be location or service id. |

**Possible responses:** `200` Request was successful; `400` Missing required argument; `401` Authorization failed; `403` Forbidden; `404` Location not found; `500` Unhandled API error

#### `GET` `/Groups/nodes/{nodeId}`
*Find node in groups*

Find node amongst groups the API caller is a `group admin` or `group support technician` in.
The API searches for nodes be they claimed or unclaimed.
It only returns a node which belongs to one of the caller's groups.
This API id being deprecated in favour of `GET /api/partners/nodes/:nodeId`.

operationId: `Group.getNodesById`

**Required to call:** `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `nodeId` | path | string | **REQUIRED** | Node id |
| `excludeUnclaimed` | query | boolean | optional | Filter out unclaimed nodes |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `403` Forbidden; `404` Node not found; `500` Unhandled API error

#### `PATCH` `/Groups/nodes/{nodeId}`
*Update node in groups*

Update a node belonging to groups the API caller is a `group admin` or `group support technician` in.

This API will also update the inventory entry. It can only update the accountId and unclaimable values.
This API id being deprecated in favour of `PATCH /api/partners/nodes/:nodeId`.

operationId: `Group.patchNodesById`

**Required to call:** `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `nodeId` | path | string | **REQUIRED** | Node id |
| `data` | body | GroupPatchNodes | optional |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `403` Forbidden; `404` Node not found; `423` This node is claimed; `500` Unhandled API error

#### `GET` `/Groups/{id}/customers/count`
*Count customers in group*

Count how many customers belong to a group.

This API is deprecated in favour of `GET /api/partners/:partnerId/customers/count`.

operationId: `Group.getCustomerCount`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Group id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Group not found; `500` Unhandled API error

#### `GET` `/Groups/{id}/customers/recent`
*Get recent customers in group*

Get the latest 100 customers assigned to group.

Returns an empty array if no customers are assigned to the group. Otherwise it returns a maximum of 100 latest customers ordered by their creation date.
This API id being deprecated in favour of `GET /api/partners/:partnerId/customers/recent`.

operationId: `Group.getRecentCustomers`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Group id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Group not found; `500` Unhandled API error

### Partner
A tag applied to Customers for labeling and administering. These APIs are only available for Admin users of the NOC.

#### `GET` `/partners/customers/search/{keyword}`
*Queries Customers with caller's partnerId.*

<div><strong>200</strong>: Success, full object returned.</div>
<div><strong>401</strong>: Authorization required.</div>
<div><strong>404</strong>: LocationId not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Partner.findCustomers`

**Required to call:** `keyword` (path), `field` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `keyword` | path | string | **REQUIRED** |  |
| `field` | query | string | **REQUIRED** |  |
| `exactMatch` | query | boolean | optional |  |
| `startsWith` | query | boolean | optional |  |
| `limit` | query | number | optional |  |
| `skip` | query | number | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/partners/{id}/customers/count`
*Queries Customers/locations/count with caller's groups.*

<div><strong>200</strong>: Success, full object returned.</div>
<div><strong>401</strong>: Authorization required.</div>
<div><strong>404</strong>: Group id not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Partner.getCustomerCount`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | partner Id |

**Possible responses:** `200` Request was successful

#### `GET` `/partners/{id}/customers/recent`
*Queries Customers/locations/count with caller's partnerId.*

<div><strong>200</strong>: Success, full object returned.</div>
<div><strong>401</strong>: Authorization required.</div>
<div><strong>404</strong>: Group id not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Partner.getRecentCustomers`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | group Id |

**Possible responses:** `200` Request was successful

#### `GET` `/partners/locations/{keyword}`
*Queries Locations with serviceId or locationId within the caller's partnerId.*

<div><strong>200</strong>: Success, full object returned.</div>
<div><strong>401</strong>: Authorization required.</div>
<div><strong>404</strong>: LocationId not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Partner.getLocations`

**Required to call:** `keyword` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `keyword` | path | string | **REQUIRED** | could be locationId, or serviceId. |

**Possible responses:** `200` Request was successful

#### `GET` `/partners/{partnerId}/nodes/{nodeId}`
*Queries Customers/locations/nodes with caller's partnerId.*

<div><strong>200</strong>: Success, full object returned.</div>
<div><strong>401</strong>: Authorization required.</div>
<div><strong>403</strong>: No right to access the node.</div>
<div><strong>404</strong>: partnerId or nodeId not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Partner.getNodesByIdForIntegrationUser`

**Required to call:** `partnerId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `partnerId` | path | string | **REQUIRED** | partner Id |
| `nodeId` | path | string | **REQUIRED** | node Id |
| `excludeUnclaimed` | query | boolean | optional | whether to filter out unclaimed nodes |

**Possible responses:** `200` Request was successful

#### `GET` `/partners/{partnerId}/customers/search/{keyword}`
*Queries Customers with caller's partnerId.*

<div><strong>200</strong>: Success, full object returned.</div>
<div><strong>401</strong>: Authorization required.</div>
<div><strong>403</strong>: Not allowed to access partner.</div>
<div><strong>404</strong>: partnerId or nodeId not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Partner.findCustomersForIntegrationUser`

**Required to call:** `partnerId` (path), `keyword` (path), `field` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `partnerId` | path | string | **REQUIRED** | partner Id |
| `keyword` | path | string | **REQUIRED** |  |
| `field` | query | string | **REQUIRED** |  |
| `exactMatch` | query | boolean | optional |  |
| `startsWith` | query | boolean | optional |  |
| `limit` | query | number | optional |  |
| `skip` | query | number | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/partners/nodes/{nodeId}`
*Queries Customers/locations/nodes with caller's partnerId.*

<div><strong>200</strong>: Success, full object returned.</div>
<div><strong>401</strong>: Authorization required.</div>
<div><strong>403</strong>: No right to access the node.</div>
<div><strong>404</strong>: LocationId not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Partner.getNodesById`

**Required to call:** `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `nodeId` | path | string | **REQUIRED** | node Id |
| `excludeUnclaimed` | query | boolean | optional | whether to filter out unclaimed nodes |

**Possible responses:** `200` Request was successful

#### `DELETE` `/partners/nodes/{nodeId}`
*Delete a node from inventory service.*

Deletes a node from inventory service.
If the node is claimed, it will throw an error.
If the node doesn't belong to the partner, it will throw an error.

operationId: `Partner.deleteNodeById`

**Required to call:** `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `nodeId` | path | string | **REQUIRED** | node Id |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `403` Forbidden; `423` This node is claimed.; `500` Unhandled API error

#### `PATCH` `/partners/nodes/{nodeId}`
*Queries Customers/locations/nodes with caller's partnerId, and update it.*

<div><strong>200</strong>: Success, full object returned.</div>
<div><strong>401</strong>: Authorization required.</div>
<div><strong>404</strong>: LocationId not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Partner.patchNodesById`

**Required to call:** `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `nodeId` | path | string | **REQUIRED** | node Id |
| `accountId` | formData | string | optional | accountId |
| `unclaimable` | formData | string | optional | unclaimable |

**Possible responses:** `200` Request was successful

### Cohort
Internal APIs for managing Cohort configurations

#### `GET` `/Cohorts/{cohortId}`
*Gets the cohort config by cohortId*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required.</div>
<div><strong>404</strong>: Cohort config not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Cohort.getCohortConfig`

**Required to call:** `cohortId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `cohortId` | path | string | **REQUIRED** | Cohort Id |

**Possible responses:** `200` Request was successful

#### `GET` `/Cohorts/aggregations/{propertyName}`
*Gets the cohort aggregations by property name*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Invalid property name.</div>
<div><strong>401</strong>: Authorization required.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Cohort.getCohortAggregations`

**Required to call:** `propertyName` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `propertyName` | path | string | **REQUIRED** | Property Name |

**Possible responses:** `200` Request was successful

### Gateway
Internal APIs for API Gateway

#### `GET` `/gateway/nodes/{nodeId}`
*Get node by id*

operationId: `Gateway.getNodeById`

**Required to call:** `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `nodeId` | path | string | **REQUIRED** | Node Id |
| `fields` | query | string | optional | Partial-response selector per the gateway fields BNF (e.g. `(*,interfaces,firmware(version),mesh,wlan,wan)`). Defaults to `*` (all top-level scalars; sub-groups omitted). |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `404` Node not found; `500` Unhandled API error

#### `PATCH` `/gateway/nodes/{nodeId}`
*Update node by id*

operationId: `Gateway.updateNodeById`

**Required to call:** `nodeId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `nodeId` | path | string | **REQUIRED** | Node Id |
| `data` | body | GatewayUpdateNodeRequestDTO | **REQUIRED** |  |
| `fields` | query | string | optional | Partial-response selector per the gateway fields BNF. Defaults to `*` (all top-level scalars). |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `422` Invalid request; `500` Unhandled API error

#### `PUT` `/gateway/nodes/{nodeId}/claim`
*Claim node by id*

operationId: `Gateway.claimNode`

**Required to call:** `nodeId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `nodeId` | path | string | **REQUIRED** | Node Id |
| `data` | body | GatewayClaimNodeRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` User or location not found; `500` Unhandled API error

#### `PUT` `/gateway/nodes/{nodeId}/unclaim`
*Unclaim node by id*

operationId: `Gateway.unclaimNode`

**Required to call:** `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `nodeId` | path | string | **REQUIRED** | Node Id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Node not found; `500` Unhandled API error

#### `PUT` `/gateway/nodes/{nodeId}/reboot`
*Reboot node by id*

operationId: `Gateway.rebootNode`

**Required to call:** `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `nodeId` | path | string | **REQUIRED** | Node Id |
| `delay` | query | number | optional | Reboot delay in seconds |

**Possible responses:** `202` Request was successful; `401` Authorization failed; `422` Invalid request; `500` Unhandled API error

#### `GET` `/gateway/locations/{locationId}/nodes`
*Get nodes for a location*

operationId: `Gateway.getLocationNodes`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** | Location Id |
| `fields` | query | string | optional | Partial-response selector per the gateway fields BNF (e.g. `(*,interfaces,firmware,mesh,wlan,wan)`). Defaults to `*` (all top-level scalars; sub-groups omitted). |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `404` Location not found; `500` Unhandled API error

#### `PUT` `/gateway/locations/{locationId}/nodes/unclaim`
*Unclaim all nodes at a location*

operationId: `Gateway.unclaimAllLocationNodes`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** | Location Id |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `404` Location not found; `500` Unhandled API error

#### `GET` `/gateway/users/{userId}/locations`
*Get locations for a user*

operationId: `Gateway.getUserLocations`

**Required to call:** `userId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `userId` | path | string | **REQUIRED** | User Id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` User not found; `500` Unhandled API error

#### `POST` `/gateway/users/{userId}/locations`
*Create location for a user*

operationId: `Gateway.createUserLocation`

**Required to call:** `userId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `userId` | path | string | **REQUIRED** | User Id |
| `data` | body | GatewayCreateLocationRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` User not found; `422` Invalid request; `500` Unhandled API error

#### `GET` `/gateway/locations/{locationId}`
*Get location by id*

operationId: `Gateway.getLocationById`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** | Location Id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Location not found; `500` Unhandled API error

#### `DELETE` `/gateway/locations/{locationId}`
*Delete location by id*

operationId: `Gateway.deleteLocationById`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** | Location Id |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `404` Location not found; `500` Unhandled API error

#### `PATCH` `/gateway/locations/{locationId}`
*Update location by id*

operationId: `Gateway.updateLocationById`

**Required to call:** `locationId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** | Location Id |
| `data` | body | GatewayUpdateLocationRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Location not found or partner forbids location type; `422` Invalid request; `500` Unhandled API error

#### `PUT` `/gateway/locations/{locationId}/onboarding/status`
*Set the onboarding status for a location.*

operationId: `Gateway.setLocationOnboardingStatus`

**Required to call:** `locationId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** | Location Id |
| `data` | body | GatewaySetOnboardingStatusRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Location not found; `422` Invalid request; `500` Unhandled API error

#### `PUT` `/gateway/locations/{locationId}/reboot`
*Reboot all nodes at a location*

operationId: `Gateway.rebootLocation`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** | Location Id |
| `delay` | query | number | optional | Reboot delay in seconds |

**Possible responses:** `202` Request was successful; `401` Authorization failed; `404` Location not found; `422` Invalid request; `500` Unhandled API error

#### `GET` `/gateway/locations/{locationId}/devices`
*Get devices for a location*

operationId: `Gateway.getLocationDevices`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** | Location Id |
| `filter` | query | string | optional | Filter defining fields, where, include, order, offset, and limit - must be a JSON-encoded string (`{"where":{"something":"value"}}`).  See https://loopback.io/doc/en/lb3/Querying-data.html#using-stringified-json-in-rest-queries for more details. |
| `fields` | query | string | optional | Partial-response selector per the gateway fields BNF (e.g. `(*,wlan,mesh,kind(*,os(*),custom(*)))`). Defaults to `*` (all top-level scalars; sub-groups omitted). |
| `embed` | query | string | optional | Comma-separated list of sub-resources to expand inline. Supported: `bandwidth` (daily download/upload Mb per device). Unknown values are ignored. On upstream failure each device receives `bandwidth: null`. |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `404` Location not found; `500` Unhandled API error

#### `GET` `/gateway/devices/{deviceId}`
*Get device by id*

operationId: `Gateway.getDeviceById`

**Required to call:** `deviceId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `deviceId` | path | string | **REQUIRED** | Device Id |
| `fields` | query | string | optional | Partial-response selector per the gateway fields BNF (e.g. `(*,wlan,mesh,kind(*,os(*),custom(*)))`). Defaults to `*` (all top-level scalars; sub-groups omitted). |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `404` Device not found; `500` Unhandled API error

#### `DELETE` `/gateway/devices/{deviceId}`
*Delete device by id*

operationId: `Gateway.deleteDeviceById`

**Required to call:** `deviceId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `deviceId` | path | string | **REQUIRED** | Device Id |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `404` Device not found; `500` Unhandled API error

#### `PATCH` `/gateway/devices/{deviceId}`
*Update device by id*

operationId: `Gateway.updateDeviceById`

**Required to call:** `deviceId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `deviceId` | path | string | **REQUIRED** | Device Id |
| `data` | body | GatewayUpdateDeviceRequestDTO | **REQUIRED** |  |
| `fields` | query | string | optional | Partial-response selector per the gateway fields BNF. Defaults to `*` (all top-level scalars). |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `404` Device not found; `422` Invalid request; `500` Unhandled API error

#### `PUT` `/gateway/devices/{deviceId}/forced-steer`
*Force a device to use the 2.4Ghz band with auto expire.*

operationId: `Gateway.setDeviceForcedSteer`

**Required to call:** `deviceId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `deviceId` | path | string | **REQUIRED** | Device Id |
| `data` | body | GatewaySetForcedSteerRequestDTO | **REQUIRED** |  |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `404` Device not found; `422` Invalid request; `500` Unhandled API error

#### `DELETE` `/gateway/devices/{deviceId}/forced-steer`
*Disable 2.4Ghz band enforcement early.*

operationId: `Gateway.deleteDeviceForcedSteer`

**Required to call:** `deviceId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `deviceId` | path | string | **REQUIRED** | Device Id |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `404` Device not found; `500` Unhandled API error

#### `GET` `/gateway/locations/{locationId}/wans`
*List WANs for a location*

operationId: `Gateway.getLocationWans`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** | Location Id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Location not found; `500` Unhandled API error

#### `GET` `/gateway/wans/{wanId}`
*Get a WAN by id*

operationId: `Gateway.getWanById`

**Required to call:** `wanId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `wanId` | path | string | **REQUIRED** | WAN Id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` WAN not found; `500` Unhandled API error

#### `PATCH` `/gateway/wans/{wanId}`
*Update a WAN by id*

operationId: `Gateway.updateWanById`

**Required to call:** `wanId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `wanId` | path | string | **REQUIRED** | WAN Id |
| `data` | body | GatewayUpdateWanConfigRequestDTO | **REQUIRED** |  |

**Possible responses:** `202` Request was successful; `401` Authorization failed; `404` WAN not found; `422` Invalid request; `500` Unhandled API error

#### `POST` `/gateway/wans/{wanId}/speed-tests`
*Start a speed test on a WAN*

operationId: `Gateway.startWanSpeedTest`

**Required to call:** `wanId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `wanId` | path | string | **REQUIRED** | WAN Id |

**Possible responses:** `202` Request was successful; `401` Authorization failed; `403` Forbidden; `404` WAN not found; `500` Unhandled API error

#### `GET` `/gateway/wans/{wanId}/speed-tests/latest`
*Get the latest speed test for a WAN*

operationId: `Gateway.getLatestWanSpeedTest`

**Required to call:** `wanId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `wanId` | path | string | **REQUIRED** | WAN Id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `403` Forbidden; `404` Not Found; `500` Unhandled API error

#### `GET` `/gateway/locations/{locationId}/nat-config`
*Get NAT config for a location*

operationId: `Gateway.getLocationNatConfig`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Location not found; `500` Unhandled API error

#### `PATCH` `/gateway/locations/{locationId}/nat-config`
*Update NAT config for a location*

operationId: `Gateway.updateLocationNatConfig`

**Required to call:** `locationId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** |  |
| `data` | body | GatewayUpdateNatConfigRequestDTO | **REQUIRED** |  |

**Possible responses:** `202` Request was successful; `401` Authorization failed; `404` Location not found; `422` Invalid request; `500` Unhandled API error

#### `GET` `/gateway/locations/{locationId}/networks`
*Get networks for a location*

operationId: `Gateway.getLocationNetworks`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** | Location Id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Location not found; `500` Unhandled API error

#### `GET` `/gateway/networks/{networkId}`
*Get network by id*

operationId: `Gateway.getNetworkById`

**Required to call:** `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `networkId` | path | string | **REQUIRED** | Network Id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Network not found; `500` Unhandled API error

#### `PATCH` `/gateway/networks/{networkId}`
*Update network config by network id*

operationId: `Gateway.patchByNetworkId`

**Required to call:** `networkId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `networkId` | path | string | **REQUIRED** | Network Id |
| `data` | body | GatewayUpdateNetworkRequestDTO | **REQUIRED** |  |

**Possible responses:** `202` Request was successful; `401` Authorization failed; `404` Network not found; `422` Invalid request; `500` Unhandled API error

#### `GET` `/gateway/networks/{networkId}/ipv4/dhcp-reservations`
*Get IPv4 DHCP reservations by network id*

operationId: `Gateway.getIpv4DhcpReservationsByNetworkId`

**Required to call:** `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `networkId` | path | string | **REQUIRED** | Network Id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Network not found; `422` Invalid request; `500` Unhandled API error

#### `PATCH` `/gateway/networks/{networkId}/ipv4/dhcp-reservations`
*Update IPv4 DHCP reservations by network id*

operationId: `Gateway.patchIpv4DhcpReservationsByNetworkId`

**Required to call:** `networkId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `networkId` | path | string | **REQUIRED** | Network Id |
| `data` | body | array | **REQUIRED** |  |

**Possible responses:** `202` Request was successful; `401` Authorization failed; `404` Network not found; `422` Invalid request; `500` Unhandled API error

#### `GET` `/gateway/networks/{networkId}/ipv4/dhcp-leases`
*Get IPv4 DHCP leases by network id*

operationId: `Gateway.getIpv4DhcpLeasesByNetworkId`

**Required to call:** `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `networkId` | path | string | **REQUIRED** | Network Id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Network not found; `422` Invalid request; `500` Unhandled API error

#### `GET` `/gateway/networks/{networkId}/authorized-clients`
*Get captive portal authorized clients for a network*

operationId: `Gateway.getNetworkAuthorizedClients`

**Required to call:** `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `networkId` | path | string | **REQUIRED** | Network Id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Network not found; `422` Invalid request; `500` Unhandled API error

#### `POST` `/gateway/networks/{networkId}/authorized-clients`
*Authorize a captive portal client on a network*

operationId: `Gateway.createNetworkAuthorizedClient`

**Required to call:** `networkId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `networkId` | path | string | **REQUIRED** | Network Id |
| `data` | body | GatewayCreateAuthorizedClientRequestDTO | **REQUIRED** |  |

**Possible responses:** `201` Request was successful; `401` Authorization failed; `404` Not Found; `422` Invalid request; `500` Unhandled API error

#### `GET` `/gateway/locations/{locationId}/wlans`
*Get WLANs for a location*

operationId: `Gateway.getLocationWlans`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** | Location Id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Location not found; `500` Unhandled API error

#### `POST` `/gateway/locations/{locationId}/wlans`
*Create a WLAN for a location*

operationId: `Gateway.createLocationWlan`

**Required to call:** `locationId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** | Location Id |
| `data` | body | GatewayCreateWlanRequestDTO | **REQUIRED** |  |

**Possible responses:** `202` Request was successful; `401` Authorization failed; `404` Location not found; `409` Conflict; `422` Invalid request; `500` Unhandled API error

#### `GET` `/gateway/wlans/{wlanId}`
*Get WLAN by id*

operationId: `Gateway.getWlanById`

**Required to call:** `wlanId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `wlanId` | path | string | **REQUIRED** | WLAN Id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` WLAN not found; `500` Unhandled API error

#### `PATCH` `/gateway/wlans/{wlanId}`
*Patch WLAN by id*

operationId: `Gateway.patchWlanById`

**Required to call:** `wlanId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `wlanId` | path | string | **REQUIRED** | WLAN Id |
| `data` | body | GatewayUpdateWlanRequestDTO | **REQUIRED** |  |

**Possible responses:** `202` Request was successful; `401` Authorization failed; `404` WLAN not found; `422` Invalid request; `500` Unhandled API error

#### `GET` `/gateway/locations/{locationId}/features`
*Get features for a location*

operationId: `Gateway.getLocationFeatures`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** | Location Id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Location not found; `500` Unhandled API error; `501` Not Implemented

#### `PATCH` `/gateway/locations/{locationId}/features`
*Update features for a location*

operationId: `Gateway.updateLocationFeatures`

**Required to call:** `locationId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** | Location Id |
| `data` | body | Gateway | **REQUIRED** | Location features update payload |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Location not found; `500` Unhandled API error; `501` Not Implemented

#### `GET` `/gateway/locations/{locationId}/capabilities`
*Get capabilities for a location*

operationId: `Gateway.getLocationCapabilities`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** | Location Id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Location not found; `500` Unhandled API error

#### `GET` `/gateway/opa/wlans/{wlanId}`
*Get partner id for a WLAN*

operationId: `Gateway.getOpaWlan`

**Required to call:** `wlanId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `wlanId` | path | string | **REQUIRED** | WLAN Id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` WLAN not found; `500` Unhandled API error

#### `GET` `/gateway/opa/networks/{networkId}`
*Get partner id for a network*

operationId: `Gateway.getOpaNetwork`

**Required to call:** `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `networkId` | path | string | **REQUIRED** | Network Id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Network not found; `500` Unhandled API error

#### `GET` `/gateway/opa/wans/{wanId}`
*Get partner id for a WAN*

operationId: `Gateway.getOpaWan`

**Required to call:** `wanId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `wanId` | path | string | **REQUIRED** | WAN Id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` WAN not found; `500` Unhandled API error

#### `GET` `/gateway/opa/devices/{deviceId}`
*Get partner id for a device*

operationId: `Gateway.getOpaDevice`

**Required to call:** `deviceId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `deviceId` | path | string | **REQUIRED** | Device Id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Device not found; `500` Unhandled API error

#### `POST` `/gateway/users`
*Create a new user*

operationId: `Gateway.createUser`

**Required to call:** `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `data` | body | GatewayCreateUserRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `422` Invalid request; `500` Unhandled API error

#### `POST` `/gateway/users/{userId}/verify-email`
*Send a verification email to the user identified by userId*

operationId: `Gateway.verifyEmailByUserId`

**Required to call:** `userId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `userId` | path | string | **REQUIRED** | User Id |
| `body` | body | object | optional |  |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `403` Forbidden; `404` User not found; `409` Conflict; `422` Invalid request; `500` Unhandled API error

#### `GET` `/gateway/users/search`
*Search users (gateway facade over Customer.searchV2 that returns LocationType instead of profile)*

operationId: `Gateway.searchUsers`

**Required to call:** `searchString` (query), `searchEntities` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `searchString` | query | string | **REQUIRED** | Search term |
| `searchEntities` | query | string | **REQUIRED** |  |
| `exactMatch` | query | boolean | optional | Only look for exact matches to keyword |
| `partnerId` | query | string | optional | Restrict the search to a single accessible partner |

**Possible responses:** `200` Request was successful; `400` Missing required argument; `401` Authorization failed; `403` Forbidden; `500` Unhandled API error

#### `POST` `/gateway/users/{userId}/reset-password`
*Send a password reset email to the user identified by userId*

operationId: `Gateway.resetPasswordByUserId`

**Required to call:** `userId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `userId` | path | string | **REQUIRED** | User Id |
| `body` | body | object | optional |  |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `403` Forbidden; `404` User not found; `422` Invalid request; `500` Unhandled API error

### Job
Represents a background job in the system. This model is used to track the status and progress of asynchronous tasks that are executed in the background. Each job has a status, message, timestamps for creation and updates, and an optional partnerId to associate the job with a specific partner or client.

#### `GET` `/Jobs/{id}`
*Find a model instance by {{id}} from the data source.*

operationId: `Job.findById`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Model id |
| `filter` | query | string | optional | Filter defining fields and include - must be a JSON-encoded string ({"something":"value"}) |

**Possible responses:** `200` Request was successful

### Customer
A Customer is initialized with a default location.

#### `GET` `/Customers/{id}/termsAndPrivacyAccepted`
*Fetches hasOne relation termsAndPrivacyAccepted.*

operationId: `Customer.prototype.__get__termsAndPrivacyAccepted`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `refresh` | query | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/termsAndPrivacyAccepted`
*Update a terms and privacy acceptance for customer.*

<div><strong>200</strong>: Success, terms and privacy updated.</div>
<div><strong>422</strong>: Input validation failed.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.updateTermsAndPrivacy`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `termsDocumentId` | formData | number | optional |  |
| `privacyDocumentId` | formData | number | optional |  |
| `termsAcceptedAt` | formData | string | optional |  |
| `privacyAcceptedAt` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/accessTokens`
*Creates a new instance in accessTokens of this model.*

operationId: `Customer.prototype.__create__accessTokens`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `data` | body | AccessToken | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/roles`
*Queries roles of Customer.*

operationId: `Customer.prototype.__get__roles`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `filter` | query | string | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}`
*Find a model instance by {{id}} from the data source.*

operationId: `Customer.findById`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Model id |
| `filter` | query | string | optional | Filter defining fields and include - must be a JSON-encoded string ({"something":"value"}) |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}`
*Patch attributes for a model instance and persist it into the data source.*

operationId: `Customer.prototype.patchAttributes__put_Customers_{id}`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `data` | body | Customer | optional | An object of model property name/value pairs |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}`
*Delete a model instance by {{id}} from the data source.*

operationId: `Customer.prototype.deleteCustomer`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `403` Forbidden; `500` Unhandled API error

#### `PATCH` `/Customers/{id}`
*Patch attributes for a model instance and persist it into the data source.*

operationId: `Customer.prototype.patchAttributes__patch_Customers_{id}`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `data` | body | Customer | optional | An object of model property name/value pairs |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers`
*Find all instances of the model matched by filter from the data source.*

operationId: `Customer.find`

**Required to call:** none

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `filter` | query | string | optional | Filter defining fields, where, include, order, offset, and limit - must be a JSON-encoded string (`{"where":{"something":"value"}}`).  See https://loopback.io/doc/en/lb3/Querying-data.html#using-stringified-json-in-rest-queries for more details. |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers`
*Create a customer.*

<div><strong>200</strong>: Success, customer created.</div>
<div><strong>422</strong>: Input validation failed.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.customCreate`

**Required to call:** none

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `email` | formData | string | optional |  |
| `password` | formData | string | optional |  |
| `name` | formData | string | optional |  |
| `firstName` | formData | string | optional |  |
| `lastName` | formData | string | optional |  |
| `partnerId` | formData | string | optional |  |
| `person` | formData | string | optional | Person object should contain object profile with field type (String) |
| `location` | formData | string | optional | Location object should contain field 'name' (String) |
| `notificationOptions` | formData | string | optional |  |
| `passwordLessToken` | formData | boolean | optional |  |
| `source` | formData | string | optional |  |
| `accountId` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/count`
*Count instances of the model matched by where from the data source.*

operationId: `Customer.count`

**Required to call:** none

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `where` | query | string | optional | Criteria to match model instances |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/login`
*Login a user with username/email and password.*

operationId: `Customer.login`

**Required to call:** `credentials` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `credentials` | body | object | **REQUIRED** |  |
| `include` | query | string | optional | Related objects to include in the response. See the description of return value for more details. |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/logout`
*Logout a user with access token.*

operationId: `Customer.logout__post_Customers_logout`

**Parameters:** none

**Possible responses:** `204` Request was successful

#### `GET` `/Customers/confirm`
*Confirm a user registration with identity verification token.*

operationId: `Customer.confirm`

**Required to call:** `uid` (query), `token` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `uid` | query | string | **REQUIRED** |  |
| `token` | query | string | **REQUIRED** |  |
| `redirect` | query | string | optional |  |

**Possible responses:** `204` Request was successful

#### `POST` `/Customers/reset`
*Reset password for a user with email.*

operationId: `Customer.resetPassword`

**Required to call:** `options` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `options` | body | object | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/backhaul`
*Retrieve location's backhaul configuration.*

operationId: `Customer.prototype.getBackhaul`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/backhaul`
*Toggle secure backhaul for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putBackhaul`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mode` | formData | string | optional | auto \|\| enable \|\| disable |
| `dynamicBeacon` | formData | string | optional | A valid state for the dynamic beaconing setting. Either auto, enable, or disable |
| `wds` | formData | string | optional | auto \|\| enable \|\| disable |
| `wpaMode` | formData | string | optional | auto \|\| psk2 \|\| sae-mixed |
| `hitlessTopology` | formData | string | optional | auto \|\| enable \|\| disable |
| `limitOnboardingRadiosMode` | formData | string | optional | auto \|\| enable \|\| disable |
| `topologySnapshot` | formData | string | optional | auto \|\| enable \|\| disable |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/ipv6`
*Retrieve location's IPv6 configuration.*

operationId: `Customer.prototype.getIPv6`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/ipv6`
*Update location's IPv6 configuration.*

operationId: `Customer.prototype.patchIPv6`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `mode` | formData | string | optional |  |
| `dns` | formData | string | optional |  |
| `addressingConfig` | formData | string | optional |  |
| `ula` | formData | string | optional |  |
| `prefix` | formData | string | optional |  |
| `inboundConnections` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/proximity`
*Get location proximity configuration.*

Retrieves the proximity zones for a location. The response can contain mix of default and custom zones.

Default zones are dynamically generated from nodes in the location. Default zones have an ID which is the same as node ID, and the name is the node nickname. Custom zones are created by the user and have a unique ID and name.

operationId: `Customer.prototype.getProximity`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Location not found; `500` Unhandled API error

#### `POST` `/Customers/{id}/locations/{locationId}/proximity/zones`
*Create custom proximity zone*

Creates a custom proximity zone for a location. The response contains the updated proximity zone.

If any of the nodes do not exist, a 404 error will be returned.
If node belongs to a zone and node is assigned to another zone, node will be removed from the previous zone and added to the new zone.
Empty zones will be removed from the location.

operationId: `Customer.prototype.createLocationProximityZone`

**Required to call:** `id` (path), `locationId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `data` | body | PostZoneRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Location or node not found; `500` Unhandled API error

#### `DELETE` `/Customers/{id}/locations/{locationId}/proximity/zones/{zoneId}`
*Deletes custom proximity zone by ID*

Deletes a custom proximity zone for a location.

If the zone does not exist, a 404 error will be returned.

operationId: `Customer.prototype.deleteLocationProximityZone`

**Required to call:** `id` (path), `locationId` (path), `zoneId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `zoneId` | path | string | **REQUIRED** | Zone ID |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `404` Location or zone not found; `500` Unhandled API error

#### `PATCH` `/Customers/{id}/locations/{locationId}/proximity/zones/{zoneId}`
*Update proximity zone by ID*

Updates a proximity zone for a location. The response contains the updated proximity zone.

If any of the zones or nodes do not exist, a 404 error will be returned.
If node belongs to a zone and node is assigned to another zone, node will be removed from the previous zone and added to the updated zone.
Empty zones will be removed from the location.

operationId: `Customer.prototype.patchLocationProximityZone`

**Required to call:** `id` (path), `locationId` (path), `zoneId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `zoneId` | path | string | **REQUIRED** | Zone ID |
| `data` | body | PatchZoneRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `400` Missing required argument; `401` Authorization failed; `404` Location, zone or node not found; `500` Unhandled API error

#### `POST` `/Customers/{id}/locations/{locationId}/proximity/devices/{mac}/batchReport`
*Publish proximity batch report to Kafka*

Publishes proximity BLE RSSI batch report to Kafka.

operationId: `Customer.prototype.publishProximityBatchReport`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** | Device MAC address |
| `data` | body | PostProximityBatchReportRequestDTO | **REQUIRED** |  |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `404` Location or device not found; `500` Unhandled API error

#### `POST` `/Customers/{id}/locations/{locationId}/proximity/devices/{mac}/groundTruth`
*Publish proximity ground truth to Kafka*

Publishes proximity ground truth to Kafka.

operationId: `Customer.prototype.publishProximityGroundTruth`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** | Device MAC address |
| `data` | body | PostProximityGroundTruthRequestDTO | **REQUIRED** |  |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `404` Location or device not found; `500` Unhandled API error

#### `GET` `/Customers/{id}/locations/{locationId}/config/dynamicFronthauls`
*Get location fronthaul.*

Gets a merged cohort and location dynamic fronthauls configuration on a specified location.


operationId: `Customer.prototype.getFronthaulLocationState`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Customer or location not found; `500` Unhandled API error

#### `GET` `/Customers/{id}/locations/{locationId}/config/fronthauls`
*Get Fronthauls Configuration.*

Gets a Cohort Fronthauls Configuration on a specified location.


operationId: `Customer.prototype.getCohortFronthauls`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Customer or location not found; `500` Unhandled API error

#### `GET` `/Customers/{id}/locations/{locationId}/config/fronthaulOverrides`
*Get Cohort Fronthauls Override Configuration.*

Gets a Cohort Fronthauls Override Configuration on a specified location.


operationId: `Customer.prototype.getCohortFronthaulOverrides`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Customer or location not found; `500` Unhandled API error

#### `PATCH` `/Customers/{id}/locations/{locationId}/config/fronthaulOverrides`
*Override Cohort Fronthauls Configuration.*

Overrides a Cohort Fronthauls Configuration on a specified location.

You need to provide a Passpoint config.

operationId: `Customer.prototype.patchCohortFronthaulOverrides`

**Required to call:** `id` (path), `locationId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `data` | body | FronthaulOverridesRequestDTO | **REQUIRED** |  |

**Possible responses:** `202` Request was successful; `401` Authorization failed; `404` Customer or location not found; `422` Invalid request; `500` Unhandled API error

#### `DELETE` `/Customers/{id}/locations/{locationId}/config/fronthaulOverrides/{networkId}`
*Clear Cohort Fronthauls Override Configuration.*

Clears the Cohort Fronthauls Override Configuration for a network on a specified location,
resetting it back to the cohort configuration.


operationId: `Customer.prototype.deleteCohortFronthaulOverrides`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** | Network ID |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `404` Customer or location not found; `500` Unhandled API error

#### `GET` `/Customers/{id}/locations/{locationId}/states/dynamicFronthauls`
*Get Dyanmic Fronthaul States.*

Gets a Dynamic Fronthaul States on a specified location.


operationId: `Customer.prototype.getDynamicFronthaulStates`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Customer or location not found; `500` Unhandled API error

#### `GET` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/{networkId}/uiConfig`
*Get guest captive portal UI configuration.*

Gets guest captive portal UI configuration for specified location and network.


operationId: `Customer.prototype.getGuestCaptivePortalUIConfig`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** | Network ID |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Customer, location, network or UI config not found; `500` Unhandled API error

#### `PUT` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/{networkId}/uiConfig`
*Put guest captive portal UI configuration.*

Puts guest captive portal UI configuration for specified location and network.


operationId: `Customer.prototype.putGuestCaptivePortalUIConfig`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** | Network ID |
| `data` | body | PutGuestCaptivePortalUIConfigRequestDTO | **REQUIRED** |  |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `404` Customer, location, or network not found; `422` Invalid request; `500` Unhandled API error

#### `PATCH` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/{networkId}/uiConfig`
*Patch guest captive portal UI configuration.*

Patches guest captive portal UI configuration for specified location and network.


operationId: `Customer.prototype.patchGuestCaptivePortalUIConfig`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** | Network ID |
| `data` | body | PatchGuestCaptivePortalUIConfigRequestDTO | **REQUIRED** |  |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `404` Customer, location, or network not found; `422` Invalid request; `500` Unhandled API error

#### `GET` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/{networkId}/uiConfigPublic`
*Get public guest captive portal UI configuration.*

Gets public guest captive portal UI configuration for specified location and network.


operationId: `Customer.prototype.getGuestCaptivePortalUIConfigPublic`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** | Network ID |

**Possible responses:** `200` Request was successful; `404` Customer, location, network or UI config not found; `500` Unhandled API error

#### `POST` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/uiConfig/images`
*Upload image for guest captive portal UI.*

Uploads image to storage for guest captive portal UI for specified location and network.


operationId: `Customer.prototype.postGuestCaptivePortalUIConfigImage`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `404` Customer, location, network or UI config not found; `500` Unhandled API error

#### `GET` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/uiConfig/brands/{brandId}`
*Get guest captive portal brand details.*

Gets guest captive portal brand details.


operationId: `Customer.prototype.getGuestCaptivePortalUIConfigBrandById`

**Required to call:** `id` (path), `locationId` (path), `brandId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `brandId` | path | string | **REQUIRED** | Brand ID |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Customer, location, or brand not found; `500` Unhandled API error

#### `PUT` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/{networkId}/sessions/{sessionId}/login`
*Login to guest captive portal session.*

Logins to guest captive portal session.


operationId: `Customer.prototype.loginGuestCaptivePortalSession`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `sessionId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** | Network ID |
| `sessionId` | path | string | **REQUIRED** | Session ID |
| `data` | body | GuestCaptivePortalSessionLoginDTO | **REQUIRED** |  |

**Possible responses:** `204` Request was successful; `400` Incorrect request; `404` Customer, location, network or session not found; `429` Too Many Requests; `500` Unhandled API error

#### `PUT` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/{networkId}/sessions/{sessionId}/verify`
*Verify guest captive portal session phone number.*

Verifies guest captive portal phone number.


operationId: `Customer.prototype.verifyGuestCaptivePortalSession`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `sessionId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** | Network ID |
| `sessionId` | path | string | **REQUIRED** | Session ID |
| `data` | body | GuestCaptivePortalSessionVerifyRequestDTO | **REQUIRED** |  |

**Possible responses:** `204` Request was successful; `400` Incorrect request; `404` Customer, location, network or session not found; `500` Unhandled API error

#### `PUT` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/{networkId}/sessions/{sessionId}/authorize`
*Authorize guest captive portal session and give internet access to client.*

Authorizes guest captive portal session and gives internet access to client.


operationId: `Customer.prototype.authorizeGuestCaptivePortalSession`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `sessionId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** | Network ID |
| `sessionId` | path | string | **REQUIRED** | Session ID |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `404` Customer, location or session not found; `500` Unhandled API error

#### `PUT` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/{networkId}/migrate`
*Migrate guest captive portal from MyWifi to Plume hosted solution.*

Migrates guest captive portal from MyWifi to Plume hosted solution.


operationId: `Customer.prototype.migrateGuestCaptivePortal`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** | Network ID |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `404` Customer, location, or network not found; `500` Unhandled API error

#### `GET` `/Customers/{id}/locations/{locationId}/serviceSets`
*Get service sets for a location.*

Gets all service sets configured for the specified location.


operationId: `Customer.prototype.getServiceSets`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Model not found; `500` Unhandled API error; `501` Not Implemented

#### `POST` `/Customers/{id}/locations/{locationId}/serviceSets`
*Create a new service set.*

Creates a new service set for the specified location.


operationId: `Customer.prototype.postServiceSet`

**Required to call:** `id` (path), `locationId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `data` | body | PostServiceSetRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `404` Customer or location not found; `422` Invalid request; `500` Unhandled API error; `501` Not Implemented

#### `PATCH` `/Customers/{id}/locations/{locationId}/serviceSets/{serviceSetId}`
*Update an existing service set.*

Updates an existing service set for the specified location.


operationId: `Customer.prototype.patchServiceSet`

**Required to call:** `id` (path), `locationId` (path), `serviceSetId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `serviceSetId` | path | string | **REQUIRED** | Service Set ID |
| `data` | body | PatchServiceSetRequestDTO | **REQUIRED** |  |

**Possible responses:** `204` Request was successful; `400` Incorrect request; `401` Authorization failed; `404` Customer, location, or service set not found; `422` Invalid request; `500` Unhandled API error; `501` Not Implemented

#### `GET` `/Customers/{id}/locations/{locationId}/focuses`
*Get all focuses.*

<div><strong>200</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getFocuses`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `freezeMigrationVersion` | query | number | optional |  |
| `migrateFreezes` | query | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/focuses`
*Create a focus.*

<div><strong>200</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>404</strong>: Network does not exist (when networkId and vapType are provided).</div>
<div><strong>422</strong>: Input validation failed.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postFocus`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `name` | formData | string | optional |  |
| `macs` | formData | string | optional |  |
| `persons` | formData | string | optional |  |
| `groups` | formData | string | optional |  |
| `enabled` | formData | boolean | optional |  |
| `appCategoriesBlocklist` | formData | string | optional |  |
| `appsBlocklist` | formData | string | optional |  |
| `websitesBlocklist` | formData | string | optional |  |
| `timer` | formData | string | optional |  |
| `schedule` | formData | string | optional |  |
| `isResidentialGatewayManaged` | formData | boolean | optional |  |
| `isTimeout` | formData | boolean | optional |  |
| `contentCategoryIdsBlocklist` | formData | string | optional |  |
| `appsAllowlist` | formData | string | optional |  |
| `websitesAllowlist` | formData | string | optional |  |
| `networkId` | formData | string | optional |  |
| `vapType` | formData | string | optional |  |
| `appliesToAllDevices` | formData | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/focuses/{focusId}`
*Delete a focus by id.*

<div><strong>200</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>404</strong>: Focus does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteFocus`

**Required to call:** `id` (path), `locationId` (path), `focusId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `focusId` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/focuses/{focusId}`
*Update a focus by id.*

<div><strong>200</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>404</strong>: Network does not exist (when networkId and vapType are provided).</div>
<div><strong>422</strong>: Input validation failed.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchFocus`

**Required to call:** `id` (path), `locationId` (path), `focusId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `focusId` | path | string | **REQUIRED** |  |
| `name` | formData | string | optional |  |
| `macs` | formData | string | optional |  |
| `persons` | formData | string | optional |  |
| `groups` | formData | string | optional |  |
| `enabled` | formData | boolean | optional |  |
| `appCategoriesBlocklist` | formData | string | optional |  |
| `appsBlocklist` | formData | string | optional |  |
| `websitesBlocklist` | formData | string | optional |  |
| `timer` | formData | string | optional |  |
| `schedule` | formData | string | optional |  |
| `contentCategoryIdsBlocklist` | formData | string | optional |  |
| `appsAllowlist` | formData | string | optional |  |
| `websitesAllowlist` | formData | string | optional |  |
| `networkId` | formData | string | optional |  |
| `vapType` | formData | string | optional |  |
| `appliesToAllDevices` | formData | boolean | optional |  |

**Possible responses:** `204` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/revertFocusMigration`
*Reverts the migration triggered by calling GET /focuses with owner token.*

<div><strong>200</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.revertFocusMigration`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/securityPolicy/ohp/ohptokens`
*Issue an OHP JWT (RS256) for a child mobile device. The JWT encodes the device identity so Gatekeeper does not need identity request parameters.*

<div><strong>200</strong>: Returns ohpToken, refreshToken, expiresAt, expiresIn.</div>
<div><strong>401</strong>: Access token invalid or expired.</div>
<div><strong>403</strong>: locationId not owned by customerId.</div>
<div><strong>404</strong>: deviceId not found in location.</div>
<div><strong>422</strong>: Required fields missing.</div>
<div><strong>429</strong>: Rate limit exceeded.</div>

operationId: `Customer.prototype.postLocationSecurityPolicyOhpToken`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `deviceId` | formData | string | optional | DeviceId of Mobile |
| `os` | formData | string | optional | OS info, e.g. iOS Version 16.2 (Build 20C65) |
| `device` | formData | string | optional | Device model, e.g. iPhone13,1 |
| `software_version` | formData | string | optional | OS version, e.g. ios-1.2.3 |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/securityPolicy/ohp/enrollmentTokens`
*Generate a short-lived enrollment token for a location. The token is embedded in a QR code or magic link and used by the child device to enroll for OHP without a Plume account.*

<div><strong>201</strong>: Returns enrollmentToken, enrollmentUrl, jti, expiresAt.</div>
<div><strong>401</strong>: Access token invalid or expired.</div>
<div><strong>403</strong>: locationId not owned by customerId.</div>
<div><strong>429</strong>: Rate limit exceeded.</div>

operationId: `Customer.prototype.postLocationSecurityPolicyOhpEnrollmentToken`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `201` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/securityPolicy/ohp/ohptokens/refresh`
*Exchange a refresh token for a fresh OHP JWT. The server looks up the row by sha256(refreshToken), so the URL is stable across key rotations.*

<div><strong>200</strong>: Returns new ohpToken, refreshToken, expiresAt, expiresIn.</div>
<div><strong>401</strong>: Refresh token invalid, expired, or revoked.</div>
<div><strong>422</strong>: refreshToken missing from the request body.</div>

operationId: `Customer.prototype.postLocationSecurityPolicyOhpTokenRefresh`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `refreshToken` | formData | string | optional | Refresh token previously issued alongside the OHP JWT |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/securityPolicy/ohp/enrollmentTokens/{jti}`
*Revoke an OHP enrollment token by its jti. The child device can no longer exchange it for an OHP JWT.*

<div><strong>204</strong>: Token revoked (or already revoked).</div>
<div><strong>401</strong>: Access token invalid or expired.</div>
<div><strong>404</strong>: jti not found in this location.</div>

operationId: `Customer.prototype.deleteLocationSecurityPolicyOhpEnrollmentToken`

**Required to call:** `id` (path), `locationId` (path), `jti` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `jti` | path | string | **REQUIRED** | jti of the enrollment token to revoke |

**Possible responses:** `204` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/securityPolicy/ohp/ohptokens/{jti}`
*Revoke an OHP JWT by its jti. Future refresh attempts will fail; Gatekeeper consults its revocation list to reject in-flight JWTs.*

<div><strong>204</strong>: Token revoked (or already revoked).</div>
<div><strong>401</strong>: Access token invalid or expired.</div>
<div><strong>404</strong>: jti not found in this location.</div>

operationId: `Customer.prototype.deleteLocationSecurityPolicyOhpToken`

**Required to call:** `id` (path), `locationId` (path), `jti` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `jti` | path | string | **REQUIRED** | jti of the OHP JWT to revoke |

**Possible responses:** `204` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/goals`
*Get all goals.*

<div><strong>200</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getGoals`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/goals`
*Create a goal.*

<div><strong>200</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>422</strong>: Input validation failed.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postGoal`

**Required to call:** `id` (path), `locationId` (path), `name` (formData), `timeframe` (formData), `targetDeviceTimeType` (formData), `targetDeviceTimeAverageMinutes` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `name` | formData | string | **REQUIRED** |  |
| `macs` | formData | string | optional |  |
| `persons` | formData | string | optional |  |
| `groups` | formData | string | optional |  |
| `apps` | formData | string | optional |  |
| `appCategories` | formData | string | optional |  |
| `timeframe` | formData | string | **REQUIRED** |  |
| `targetDeviceTimeType` | formData | string | **REQUIRED** |  |
| `targetDeviceTimeAverageMinutes` | formData | number | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/goals/{goalId}`
*Delete a goal by id.*

<div><strong>200</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>404</strong>: Goal does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteGoal`

**Required to call:** `id` (path), `locationId` (path), `goalId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `goalId` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/goals/{goalId}`
*Update a goal by id.*

<div><strong>200</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>404</strong>: Goal does not exist.</div>
<div><strong>422</strong>: Input validation failed.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchGoal`

**Required to call:** `id` (path), `locationId` (path), `goalId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `goalId` | path | string | **REQUIRED** |  |
| `name` | formData | string | optional |  |

**Possible responses:** `204` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/goals/{goalId}/archive`
*Archive a goal by id.*

<div><strong>200</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>404</strong>: Goal does not exist.</div>
<div><strong>422</strong>: Input validation failed.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.archiveGoal`

**Required to call:** `id` (path), `locationId` (path), `goalId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `goalId` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/goals/{goalId}/deviceTimeSummary`
*Get Goal progress*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getGoalDeviceTimeSummary`

**Required to call:** `id` (path), `locationId` (path), `goalId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `goalId` | path | string | **REQUIRED** | goal ID |
| `startDate` | formData | string | optional | Progress start date - format yyyy-mm-dd |
| `endDate` | formData | string | optional | Progress end date - format yyyy-mm-dd - default today |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/nodePlacement/recommendations`
*Submit node placement recommendations for a location.*

Stores latest recommendations on the location object.


operationId: `Customer.prototype.postNodePlacementRecommendations`

**Required to call:** `id` (path), `locationId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `data` | body | PostNodePlacementRecommendationsRequestDTO | **REQUIRED** |  |

**Possible responses:** `202` Request was successful; `400` Incorrect request; `401` Authorization failed; `404` Customer or location not found; `422` Invalid request; `500` Unhandled API error; `501` Not Implemented

#### `DELETE` `/Customers/{id}/locations/{locationId}/nodePlacement/recommendations`
*Clear all node placement recommendations for a location.*

Clears every entry from nodePlacementRecommendations for the location.


operationId: `Customer.prototype.clearNodePlacementRecommendations`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `404` Customer or location not found; `500` Unhandled API error

#### `POST` `/Customers/{id}/locations/{locationId}/nodePlacement/recommendations/disable`
*Disable node placement recommendations for a location.*

operationId: `Customer.prototype.disableNodePlacementRecommendations`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `404` Customer or location not found; `500` Unhandled API error

#### `POST` `/Customers/{id}/locations/{locationId}/nodePlacement/recommendations/enable`
*Enable node placement recommendations for a location.*

operationId: `Customer.prototype.enableNodePlacementRecommendations`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `404` Customer or location not found; `500` Unhandled API error

#### `DELETE` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/nodePlacement/recommendations`
*Clear node placement recommendation for a specific node at a location.*

Removes only the entry for the given nodeId from nodePlacementRecommendations.


operationId: `Customer.prototype.clearNodePlacementRecommendationsForNode`

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `nodeId` | path | string | **REQUIRED** | Node ID |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `404` Customer or location not found; `500` Unhandled API error

#### `PUT` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/nodePlacement/recommendations/dismiss`
*Dismiss the node placement recommendation for a specific node at a location.*

Hides the recommendation in-app and stops placement notifications for that node until hideUntil.
When hideUntil is omitted the dismissal lasts 60 days from the time the request reaches the server.
Calling the same endpoint with a past hideUntil reverses the dismissal.


operationId: `Customer.prototype.dismissNodePlacementRecommendation`

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `nodeId` | path | string | **REQUIRED** | Node ID |
| `data` | body | DismissNodePlacementRecommendationRequestDTO | optional |  |

**Possible responses:** `204` Request was successful; `400` Incorrect request; `401` Authorization failed; `404` Customer, location or node not found; `500` Unhandled API error

#### `POST` `/Customers/{id}/locations/{locationId}/nodePlacement/start`
*Start node placement mode for a set of nodes at a location.*

Enables node placement mode and returns the computed state.


operationId: `Customer.prototype.startNodePlacement`

**Required to call:** `id` (path), `locationId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `data` | body | PostNodePlacementStartRequestDTO | **REQUIRED** |  |

**Possible responses:** `202` Request was successful; `400` Incorrect request; `401` Authorization failed; `404` Customer or location not found; `422` Invalid request; `500` Unhandled API error; `501` Not Implemented

#### `GET` `/Customers/{id}/locations/{locationId}/nodePlacement/state`
*Get the current node placement state for a location.*

operationId: `Customer.prototype.getNodePlacementState`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Model not found; `500` Unhandled API error

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/nodePlacement/livePlugPointAssessment`
*Get live plug point assessment for a given device mac.*

operationId: `Customer.prototype.getNodePlacementLivePlugPointAssessment`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** | Mac |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Model not found; `500` Unhandled API error

#### `POST` `/Customers/{id}/locations/{locationId}/nodePlacement/stop`
*Stop node placement mode for a set of nodes at a location.*

operationId: `Customer.prototype.stopNodePlacement`

**Required to call:** `id` (path), `locationId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `data` | body | PostNodePlacementStopRequestDTO | **REQUIRED** |  |

**Possible responses:** `202` Request was successful; `400` Incorrect request; `401` Authorization failed; `404` Customer or location not found; `422` Invalid request; `500` Unhandled API error; `501` Not Implemented

#### `POST` `/Customers/{id}/locations/{locationId}/nodePlacement/cancel`
*Cancel node placement mode for a set of nodes at a location without triggering reinforcement.*

operationId: `Customer.prototype.cancelNodePlacement`

**Required to call:** `id` (path), `locationId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `data` | body | PostNodePlacementStopRequestDTO | **REQUIRED** |  |

**Possible responses:** `202` Request was successful; `400` Incorrect request; `401` Authorization failed; `404` Customer or location not found; `422` Invalid request; `500` Unhandled API error; `501` Not Implemented

#### `POST` `/Customers/{id}/locations/{locationId}/nodePlacement/recommendations/request`
*Request node placement recommendations for a location.*

Sends a GRPC message to Overlord to request offline placement recommendations.


operationId: `Customer.prototype.requestNodePlacementRecommendations`

**Required to call:** `id` (path), `locationId` (path), `isTest` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `isTest` | formData | boolean | **REQUIRED** | Is Test Request |
| `sessionId` | formData | string | optional | Session ID |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Customer or location not found; `500` Unhandled API error

#### `POST` `/Customers/{id}/locations/{locationId}/nodePlacement/session/{sessionId}/viewed`
*Mark a node placement session as viewed by the user.*

Publishes a VIEWED engagement event to Kafka for the given placement session.


operationId: `Customer.prototype.viewNodePlacementSession`

**Required to call:** `id` (path), `locationId` (path), `sessionId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `sessionId` | path | string | **REQUIRED** | Placement session ID |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `404` Customer, location or placement session not found; `500` Unhandled API error

#### `GET` `/Customers/{id}/nodePlacement/mobile-active`
*Get mobile app activity (last login and active status) for a customer.*

Derives the last mobile login from Global auth (latest entry with isMobile=true).
When auth logs are empty, falls back to the latest non-refresh access token creation date.
isActive is true when lastLogin is within the last 30 days.

operationId: `Customer.prototype.getMobileActive`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Customer not found; `500` Unhandled API error

#### `GET` `/Customers/v2/search`
*Search for customers across multiple entity types with optional exact match filtering*

This endpoint searches for customers based on various identifiers and returns matching results with their associated locations. Each result includes `matchingString` (the original query the caller sent) and `matchedValue` (the full stored value of the field that produced the match, useful for partial/regex searches where the stored value differs from the query).

**Search Entities**
Supported search entities: nodeId, locationId, customerId, name, email, accountId, serviceId

**Exact Match Requirements**
The following search entities ONLY work if the exact value is provided (ObjectID limitation), otherwise they return no results:
- locationId
- customerId

Other entities (name, email, accountId, serviceId, nodeId) support both exact and partial (regex) matching.

**Search Limits**
- Maximum results per entity: 10 customers
- Maximum locations per customer: 10 locations
- Single-entity searches (nodeId, locationId, customerId with exact match): 1 result

**Authorization**
- Admin, support, and integration roles: Access to all customers
- Partner-based users: Only customers within accessible child (leaf) partner IDs (excludes FRV partners)
- Group-based users: Only customers associated with their groups
- Partner access takes precedence over group access
- Optional `partnerId` query parameter restricts the search to a single partner. For partner-based users it must be in their accessible partner list, otherwise a 403 is returned. For privileged roles it is honored without validation.

**Special Cases**
- Email search: When customer anonymization is enabled and exactMatch=true, searches both plain and hashed email addresses
- Email normalization: Email searches are case-insensitive (converted to lowercase)
- Regex escaping: Special regex characters are escaped in partial match searches
- Group search: When performing a search with a group user, the system can scan up to 50,000 customers. If this 
limit is reached and no customers are found that belong to the caller’s groups, a descriptive 400 error will be returned.

operationId: `Customer.searchV2`

**Required to call:** `searchString` (query), `searchEntities` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `searchString` | query | string | **REQUIRED** | Search term |
| `searchEntities` | query | string | **REQUIRED** |  |
| `exactMatch` | query | boolean | optional | Only look for exact matches to keyword |
| `partnerId` | query | string | optional | Restrict the search to a single accessible partner |

**Possible responses:** `200` Request was successful; `400` Missing required argument; `401` Authorization failed; `403` Forbidden; `500` Unhandled API error

#### `GET` `/Customers/{id}/locations/{locationId}/wlans`
*Get all WLAN configs for a location.*

Returns a unified list of all WLANs configured for the specified location.

The response provides a consolidated view of all WLAN configurations in a single array.

operationId: `Customer.prototype.getWlans`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Customer or location not found; `500` Unhandled API error; `501` Not Implemented

#### `POST` `/Customers/{id}/locations/{locationId}/securityPolicy/websites/batch`
*Batch add websites/IPs to allowlist/blocklist for multiple persons, groups, and devices.*

<div><strong>200</strong>: Success. Returns results for each entity.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or entity does not exist.</div>
<div><strong>422</strong>: Validation failed for one or more entries.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.batchAddSecurityPolicyWebsites`

**Required to call:** `id` (path), `locationId` (path), `body` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `body` | body | BatchSecurityPolicyWebsitesRequestDTO | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/securityPolicy/websites/batch/delete`
*Batch delete websites/IPs from allowlist/blocklist for multiple persons, groups, and devices.*

<div><strong>200</strong>: Success. Returns results for each entity.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or entity does not exist.</div>
<div><strong>422</strong>: Validation failed for one or more entries.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.batchDeleteSecurityPolicyWebsites`

**Required to call:** `id` (path), `locationId` (path), `body` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `body` | body | BatchSecurityPolicyWebsitesRequestDTO | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/securityPolicy/websites/batch/{listType}/{type}/{value}`
*Atomically reconcile one website/IP entry across entities for allowlist/blocklist.*

<div><strong>204</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing, field type is incorrect, or person/group not found.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist.</div>
<div><strong>422</strong>: Validation failed for one or more entries.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putBatchSecurityPolicyWebsiteScope`

**Required to call:** `id` (path), `locationId` (path), `listType` (path), `type` (path), `value` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `listType` | path | string | **REQUIRED** | List type: allowlist or blocklist. |
| `type` | path | string | **REQUIRED** | Entry type: fqdn, ipv4, or ipv6. |
| `value` | path | string | **REQUIRED** | Domain or IP value. |
| `body` | body | BatchSecurityPolicyWebsitesTargetsRequestDTO | optional |  |

**Possible responses:** `204` Request was successful; `undefined` Internal server error.

#### `GET` `/Customers/{id}/locations/{locationId}/websites/list`
*Get all whitelist/blacklist configurations*

<div>Get all website whitelist/blacklist configurations for a location including all levels (location, person, device, group).</div>

operationId: `Customer.prototype.getLocationWebsitesList`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful; `400` Missing required argument; `401` Authorization failed; `422` Invalid request; `500` Unhandled API error

#### `GET` `/Customers/{id}/locations/{locationId}/nodeLogs/processes`
*Get available node processes for a location.*

operationId: `Customer.prototype.getNodeProcesses`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Customer or location not found; `500` Unhandled API error

#### `GET` `/Customers/{id}/locations/{locationId}/nodeLogs`
*Get current node logging configuration for a location.*

operationId: `Customer.prototype.getNodeLogs`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Customer or location not found; `500` Unhandled API error

#### `PUT` `/Customers/{id}/locations/{locationId}/nodeLogs`
*Configure node process logging for a location.*

operationId: `Customer.prototype.putNodeLogs`

**Required to call:** `id` (path), `locationId` (path), `body` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `body` | body | PutNodeLogsRequestDTO | **REQUIRED** | Node logging configuration |

**Possible responses:** `204` Request was successful; `400` Incorrect request; `401` Authorization failed; `404` Customer or location not found; `500` Unhandled API error

#### `GET` `/Customers/search/{keyword}`
*Search the keyword on a particular field such as "accountId", "name", "email".*

<div><strong>200</strong>: Success, return the search result.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>422</strong>: "illegal field"</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.searchFields`

**Required to call:** `keyword` (path), `field` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `keyword` | path | string | **REQUIRED** |  |
| `field` | query | string | **REQUIRED** |  |
| `exactMatch` | query | boolean | optional |  |
| `startsWith` | query | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/kvConfigs`
*Retrieve all kvConfigs on a particular Node for a Location ID.*

<div><strong>200</strong>: Success, your new info looks good.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist.</div>
<div><strong>422</strong>: nodeId must be defined.</div>
<div><strong>425</strong>: nodeId must belong to the location.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getKvConfigs`

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `nodeId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/kvConfigs`
*Retrieve all kvConfigs on a particular Node for a Location ID.*

<div><strong>200</strong>: Success, your new info looks good.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist.</div>
<div><strong>422</strong>: nodeId must be defined.</div>
<div><strong>425</strong>: nodeId must belong to the location.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postKvConfigs`

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path), `module` (formData), `key` (formData), `value` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `nodeId` | path | string | **REQUIRED** |  |
| `module` | formData | string | **REQUIRED** |  |
| `key` | formData | string | **REQUIRED** |  |
| `value` | formData | string | **REQUIRED** |  |
| `persist` | formData | boolean | optional |  |
| `isSensitive` | formData | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/kvConfigs`
*Retrieve all kvConfigs on a particular Node for a Location ID.*

<div><strong>200</strong>: Success, your new info looks good.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist.</div>
<div><strong>422</strong>: nodeId must be defined.</div>
<div><strong>425</strong>: nodeId must belong to the location.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchKvConfigs`

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path), `kvConfigs` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `nodeId` | path | string | **REQUIRED** |  |
| `kvConfigs` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/vapStates`
*Retrieve all Vap State on a particular Node for a Location ID.*

<div><strong>200</strong>: Success, your new info looks good.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getVapStates`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/backhauls`
*Retrieve all Vap State on a particular Node for a Location ID.*

<div><strong>200</strong>: Success, your new info looks good.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getVapsAndStaStatesFromBackhaul`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/kvStates`
*Retrieve all kvStates on a particular Node for a Location ID.*

<div><strong>200</strong>: Success, your new info looks good.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist.</div>
<div><strong>422</strong>: nodeId must be defined.</div>
<div><strong>425</strong>: nodeId must belong to the location.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getNodeKvStates`

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `nodeId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/schedules`
*Get custom shared schedules for a given Location ID.*

<div><strong>200</strong>: Success, custom schedules list returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.listCustomSharedSchedules`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/schedules`
*Create "custom shared" schedules that shared by all persons and devices in a location.*

<div><strong>200</strong>: Success, custom shared schedules applied.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist or is not known to Plume</div>
<div><strong>422</strong>: schedules value is invalid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postCustomSharedSchedule`

**Required to call:** `id` (path), `locationId` (path), `name` (formData), `type` (formData), `schedules` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `name` | formData | string | **REQUIRED** |  |
| `type` | formData | string | **REQUIRED** |  |
| `schedules` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/schedules/{templateId}`
*Delete "custom shared" schedule shared by all persons and devices in a location.*

<div><strong>204</strong>: Success, the custom shared schedule deleted.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist or is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteCustomSharedSchedule`

**Required to call:** `id` (path), `locationId` (path), `templateId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `templateId` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/schedules/{templateId}`
*Patch a custom shared schedule freeze template for a Location ID.*

<div><strong>200</strong>: Success, your new info looks good.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist.</div>
<div><strong>422</strong>: templateId must be defined.</div>
<div><strong>422</strong>: schedules value is invalid.</div>
<div><strong>425</strong>: templateId must belong to the location.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchCustomSharedSchedule`

**Required to call:** `id` (path), `locationId` (path), `templateId` (path), `schedules` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `templateId` | path | string | **REQUIRED** |  |
| `schedules` | formData | string | **REQUIRED** |  |
| `name` | formData | string | optional |  |
| `type` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/linkedAccounts`
*link the outside account, such as Samsung user.*

<div><strong>200</strong>: Success, the outside account inserted into the customer info/object.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.linkAccount`

**Required to call:** `id` (path), `provider` (formData), `userId` (formData), `sessionToken` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `provider` | formData | string | **REQUIRED** |  |
| `userId` | formData | string | **REQUIRED** |  |
| `userName` | formData | string | optional |  |
| `userDisplayName` | formData | string | optional |  |
| `sessionToken` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/linkedAccounts/{provider}/{userId}`
*link the outside account, such as Samsung user.*

<div><strong>200</strong>: Success, the outside account inserted into the customer info/object.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteLinkedAccount`

**Required to call:** `id` (path), `provider` (path), `userId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `provider` | path | string | **REQUIRED** |  |
| `userId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/qoe/liveMode`
*Update the location qoe liveMode by api call and Kafka message*

<div><strong>200</strong>: Success, the new info looks good.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>400</strong>: enalbe and expiresAt, reportingInterval validation error.</div>
<div><strong>422</strong>: expiresAt and reportingInterval validation error.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchLocationQoeLiveMode`

**Required to call:** `id` (path), `locationId` (path), `enable` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `enable` | formData | boolean | **REQUIRED** |  |
| `expiresAt` | formData | string | optional |  |
| `reportingInterval` | formData | number | optional |  |
| `placement` | formData | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/kvConfigs/{module}/{key}`
*Delete kvConfigs with selected module and key on a particular Node for a Location ID.*

<div><strong>200</strong>: Success, your new info looks good.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist.</div>
<div><strong>422</strong>: nodeId must be defined.</div>
<div><strong>425</strong>: nodeId must belong to the location.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteKvConfigs`

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path), `module` (path), `key` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `nodeId` | path | string | **REQUIRED** |  |
| `module` | path | string | **REQUIRED** |  |
| `key` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/passwordLessToken`
*Verifies the email token and activates tokens related to it. Returns verified text with redirect to "signup complete deep link"*

<div><strong>204</strong>: Success, return new appToken and send out the email with emailToken.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>422</strong>: nodeId must be defined.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.verifyEmailPasswordlessToken`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |

**Possible responses:** `204` Request was successful

#### `POST` `/Customers/{id}/accessToken`
*Generates usable passwordless accessToken for the account with the email address.*

<div><strong>204</strong>: Success, return new appToken.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.createNewPasswordlessToken`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/refreshToken`
*Generates a new refresh token*

<div><strong>200</strong>: Success, return new refreshToken.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.createNewRefreshToken`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `accessTokenId` | formData | string | optional | Access token Id |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/persons/{personId}/profile-scoped-token`
*Mint profile-scoped token set for specific person.*

Mints access and refresh tokens with scope set to PROFILE.

This type of access token provides access to select endpoints, and is limited to personId used on creation of the token.

operationId: `Customer.prototype.mintProfileScopedTokenSet`

**Required to call:** `id` (path), `locationId` (path), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location Id |
| `personId` | path | string | **REQUIRED** | Person Id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `403` Forbidden; `404` No instance with id {personId} found for Person; `500` Unhandled API error

#### `POST` `/Customers/passwordLessToken`
*Generate two accessTokens with special scopes for the account with the email address and send a verification email.*

<div><strong>200</strong>: Success, return new appToken, refreshToken and send out the email with emailToken.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>422</strong>: Email must be defined and valid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.emailPasswordlessToken`

**Required to call:** `email` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `email` | formData | string | **REQUIRED** |  |
| `notificationOptions` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/createIpLimitedAccessToken`
*Create access token with limited privileges as defined for IP authenticated customers*

<div><strong>200</strong>: Success, response object returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.createIpLimitedAccessToken`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `ttl` | formData | number | optional |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/createReadDnsAccessToken`
*Create access token to read data related to DNS security policies*

<div><strong>200</strong>: Success, accessToken returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.createReadDnsAccessToken`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/createPatchServiceLevelAccessToken`
*Create access token to patch customer serviceLevel used by ZUORA*

<div><strong>200</strong>: Success, accessToken returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.createPatchServiceLevelAccessToken`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `ttl` | formData | number | optional |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/createGetMarketingExportDataAccessToken`
*Create access token to get marketing data by CRM for campaigns*

<div><strong>200</strong>: Success, accessToken returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.createGetMarketingExportDataAccessToken`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `ttl` | formData | number | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/firmware`
*Firmware Upgrade Status*

<div><strong>200</strong>: Success, response object returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getFirmwareUpgradeStatus`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/firmware`
*Request Firmware Upgrade for a Location ID*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putFirmwareUpgradeRequest`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/frontline/storage`
*Fetch the frontline storage for this location*

<div><strong>200</strong>: Success, HomeSecurity object returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getFrontlineStorage`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/frontline/storage`
*Create or Update the frontline storage for a Location ID*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putFrontlineStorage`

**Required to call:** `id` (path), `locationId` (path), `data` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `data` | formData | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/homeSecurity`
*Fetch the home security configuration for this location*

<div><strong>200</strong>: Success, HomeSecurity object returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getHomeSecurity`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/homeSecurity`
*Enable/disable live motion streaming and/or motion events for this location*

<div><strong>200</strong>: Success, updated HomeSecurity object returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchHomeSecurity`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `source` | formData | string | optional | Source of patch request; must be one of "user" or "geofence" |
| `liveMotionEnabled` | formData | boolean | optional |  |
| `motionEventsEnabled` | formData | boolean | optional |  |
| `homeAwayActive` | formData | boolean | optional | Enable/disable motion events based on location Homeaway state |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/homeSecurity/homeAway`
*Enable/disable homeAway wifiMotionEvents activation for this location*

<div><strong>200</strong>: Success, updated HomeSecurity object returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchHomeAwayActive`

**Required to call:** `id` (path), `locationId` (path), `homeAwayActive` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `homeAwayActive` | formData | boolean | **REQUIRED** | Enable/disable motion events based on location Homeaway state |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/homeSecurity/sensitivity`
*Configure motion event configuration for this location*

<div><strong>200</strong>: Success, updated HomeSecurity object returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchHomeSecuritySensitivity`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `cooldown` | formData | number | optional | sets required rest period for motion detected events to end, in seconds |
| `petMode` | formData | string | optional | adjusts sensitivity of motion detected events for pets; must be one of "none", "under10", "10to30", "over30" and can only be set if sensitivity = high |
| `sensitivity` | formData | string | optional | adjusts sensitivity of motion detected events; must be one of "low", "medium", "high" |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/homeSecurity/motionHistory`
*Fetch the motion density history for this location*

<div><strong>200</strong>: Success, motion density array returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getMotionHistory`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `from` | query | number | optional | UTC unix ts |
| `to` | query | number | optional | UTC unix ts, defaults to now |
| `bucket` | query | number | optional | number of seconds in density calculation window; returned data points represent % of non-zero intensity values in the window |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/homeSecurity/motionHistory/state`
*Fetch the motion state history for this location*

<div><strong>200</strong>: Success, motion state array returned (Each element of the array is in the form ["val", "unix_ts"], where "val" is one of: 
<div>0 - Not armed, not tripped</div>
<div>1 - Not armed, tripped</div>
<div>2 - Armed, not tripped</div>
<div>3 - Armed, tripped</div></div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getMotionStateHistory`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `from` | query | number | optional | UTC unix ts |
| `to` | query | number | optional | UTC unix ts, defaults to now |
| `bucket` | query | number | optional | number of seconds in density calculation window; returned data points represent % of non-zero intensity values in the window |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/homeSecurity/events/history`
*Fetch the event history for this location*

<div><strong>200</strong>: Success, event array returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getEventHistory`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `from` | query | number | optional | UTC unix ts |
| `to` | query | number | optional | UTC unix ts, defaults to now |
| `category` | query | string | optional | Filter events by category (Motion or Plume [config changes]). Multiple categories can be passed as a comma-separated string. Default is both. |
| `limit` | query | number | optional | Maximum number of events to return. Defaults to 10 |
| `sort` | query | boolean | optional | whether the returned events will be post-sorted by timestamp |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/homeSecurity/devices/sounding`
*Fetch the sounding states for eligible devices in this location*

<div><strong>200</strong>: Success, device sounding states returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDeviceSoundingState`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | query | string | optional | Optional mac address for single device lookup (fetches all devices by default) |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/homeSecurity/devices/sounding`
*Patch the sounding states for the given devices*

<div><strong>200</strong>: Success, device sounding states returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchDeviceSoundingState`

**Required to call:** `id` (path), `locationId` (path), `soundingStates` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `soundingStates` | body | object | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/wifiMotion`
*Get WifiMotion config for this location*

<div><strong>200</strong>: Success, wifiMotion object returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getWifiMotion`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/wifiMotion`
*Enable/disable WifiMotion feature for this location*

<div><strong>200</strong>: Success, updated object returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchWifiMotion`

**Required to call:** `id` (path), `locationId` (path), `auto` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `auto` | formData | boolean | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/serviceLevel`
*Get the service level for this location*

<div><strong>200</strong>: Success, return service Level object.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getServiceLevel`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/serviceLevel`
*Set the service level for this location*

<div><strong>200</strong>: Success, updated service Level object returned.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>422</strong>: Invalid 'status' value.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchServiceLevel`

**Required to call:** `id` (path), `locationId` (path), `status` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `status` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/marketingExport`
*Get detailed information of a location for CRM campaigns.*

<div><strong>200</strong>: Success, location data in response.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.marketingExport`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `wifiMotionCapable` | query | boolean | optional |  |
| `wifiMotionEnable` | query | boolean | optional |  |
| `onlineProtectionEnabled` | query | boolean | optional |  |
| `personsWithoutAssignedDevices` | query | boolean | optional |  |
| `peopleProfileEverCreated` | query | boolean | optional |  |
| `blockedSecurityEventsCountThirtyDay` | query | boolean | optional |  |
| `devicesOnlineThirtyDays` | query | boolean | optional |  |
| `mostActiveDevicesThirtyDays` | query | boolean | optional |  |
| `appTimeCapable` | query | boolean | optional |  |
| `subscription` | query | boolean | optional |  |
| `lastThirtyDaysSpeedTestAverages` | query | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/homeAway/events`
*Fetch the all the Homeaway events history for this location*

<div><strong>200</strong>: Success, event array returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getHomeAwayLocationEvents`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `from` | query | number | optional | UTC unix epoch ms, defaults to 1 week ago |
| `to` | query | number | optional | UTC unix epoch ms, defaults to now |
| `limit` | query | number | optional | Maximum number of events to return. Defaults to 100 |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/wifiNetworks`
*WiFi Networks*

<div><strong>200</strong>: Success, response object returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getWifiNetworks`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/wifiNetworksWithWpaMode`
*Get WiFi Networks with wpa mode.*

<div><strong>200</strong>: Success, response object returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getWifiNetworksWithWpaMode`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/createOrUpdateUser`
*Create or update a NOC user.*

<div><strong>200</strong>: Success, user created.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>422</strong>: Input validation failed.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.createOrUpdateUser`

**Required to call:** `email` (formData), `name` (formData), `roles` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `email` | formData | string | **REQUIRED** |  |
| `name` | formData | string | **REQUIRED** |  |
| `roles` | formData | string | **REQUIRED** |  |
| `groups` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/registerWithGroups`
*Register a customer belonging to a group or partner*

Register a customer with an email, accountId, and name. Either groupIds or partnerId needs to be defined.

We recommend you set the accountId to either a UUID or to some unique identifier that is specific to your business and can be used to uniquely identify this customer within your organisation. The minimum length is 6 characters.
Optionally, we can provide a password that needs to be at least 8 characters long, and needs to have at least two of the following: uppercase character, lowercase character, number or symbol
This API can only be called with a group admin role or using a M2M token.

operationId: `Customer.registerWithGroups`

**Required to call:** none

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `data` | body | RegisterWithGroupsRequestDTO | optional |  |

**Possible responses:** `200` Request was successful; `400` Missing required argument; `401` Authorization failed; `403` Forbidden; `422` Invalid request; `500` Unhandled API error

#### `POST` `/Customers/migratableCustomers`
*Returns a paginated list of accounts given a filter.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields are missing.</div>
<div><strong>401</strong>: Authorization required.</div>
<div><strong>422</strong>: Input validation failed.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.migratableCustomers`

**Required to call:** `where` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `where` | formData | string | **REQUIRED** |  |
| `limit` | formData | number | optional |  |
| `cursor` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/register`
*Create a customer belonging to a partner.*

You can either create a customer using accountId and partnerId, to create an "anonymous" customer. Or, you can create one with email, accountId, and partnerId.
We recommend you set the accountId to either a UUID or to some unique identifier that is specific to your business and can be used to uniquely identify this customer within your organisation. The minimum length is 6 characters.
This API can be called with admin role or with a M2M token.

operationId: `Customer.register`

**Required to call:** none

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `data` | body | RegisterRequestDTO | optional |  |

**Possible responses:** `200` Request was successful; `400` Missing required argument; `401` Authorization failed; `403` Forbidden; `422` Invalid request; `500` Unhandled API error

#### `POST` `/Customers/{id}/campaigns`
*Create a braze campaign.*

<div><strong>204</strong>: Success, campaign created.</div>
<div><strong>400</strong>: Required field is missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>422</strong>: Campaign name validation failed.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.createCampaign`

**Required to call:** `id` (path), `name` (formData), `properties` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `name` | formData | string | **REQUIRED** |  |
| `properties` | formData | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `GET` `/Customers/{id}/locations`
*Queries locations of Customer.*

<div><strong>200</strong>: Success, full object returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: LocationId not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getLocations`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `include` | query | string | optional | CSV value of objects to add to the response: summary (is the only option for now) |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations`
*Create a new location.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>400</strong>: Required field(the location name) missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.createLocation`

**Required to call:** `id` (path), `name` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `name` | formData | string | **REQUIRED** |  |
| `profile` | formData | string | optional |  |
| `serviceId` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}`
*Get a Location's combined State and Config by LocationId.*

<div><strong>200</strong>: Success, full object returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: LocationId not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.findLocationById`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `include` | query | string | optional | CSV value of objects to add to the response: summary (is the only option for now) |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}`
*Update the location name.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.updateLocationName`

**Required to call:** `id` (path), `locationId` (path), `name` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `name` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}`
*Archive a location.*

<div><strong>204</strong>: Success, location archived.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>409</strong>: Location already archived.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteLocation`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `204` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}`
*Update a Location's serviceId.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist and is not known to Plume</div>
<div><strong>422</strong>: You must specify at least one parameter to patch.</div>
<div><strong>422</strong>: Only integration role can set profile to property.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchLocation`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `serviceId` | formData | string | optional |  |
| `profile` | formData | string | optional |  |
| `name` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `HEAD` `/Customers/{id}/locations/{locationId}`
*Verify that a Customer Id has a Location Id.*

<div><strong>200</strong>: Success, no data returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: LocationId not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.hasLocationById`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/networkConfiguration/natLoopback`
*Update the location natLoopback.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchNatLoopback`

**Required to call:** `id` (path), `locationId` (path), `natLoopback` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `natLoopback` | body | NatLoopback | **REQUIRED** | natLoopback object |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/subscription`
*Get Subscription details for this location*

<div><strong>200</strong>: Success, subscription details returned</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getSubscription`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/appFacade/home`
*Retrieve timezone, capabilities, summary, ... for this location.*

<div><strong>200</strong>: Success, an array of properties returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.appFacadeHome`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `filters` | query | string | optional |  |
| `daysOffline` | query | number | optional |  |
| `showOnlyIot` | query | boolean | optional |  |
| `showAlsoIot` | query | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/uplink-status`
*Retrieve uplink status including speed test data and location uptime*

This endpoint returns the latest uplink status information for a location, including:

**Speed Test Data**
- Download speed (Mbps)
- Upload speed (Mbps)
- Timestamp of the test (ISO 8601 UTC)
- Latency/RTT (milliseconds)
- Jitter (milliseconds)
- Test status (succeeded, failed, etc.)
- Test trigger (scheduled, manual, etc.)
- ISP name

**Location Uptime**
- Gateway connection state (connected or disconnected)
- Timestamp when the connection state last changed (ISO 8601 UTC)

**Data Availability**
- Speed test data will be null if no tests have been performed
- Jitter and latency are calculated from the gateway node speed test data when available
- Uptime is calculated from the earliest connection time among all connected nodes

operationId: `Customer.prototype.getUplinkStatus`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` There are no locations with the ID "6aa0546eebcb2b0d2f36debe"; `500` Unhandled API error

#### `GET` `/Customers/{id}/locations/{locationId}/groups`
*Retrieve Device Groups for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist and is not known to Plume.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getLocationDeviceGroups`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/groups`
*Create a Device Group for a Location ID.*

Creates a Device Group on a specified location.

You need to provide a nickname for the device group.
Additionally you can provide an array of assigned devices that will be assigned to the device group.
Optionally you can provide security policy config to be applied for this device group.

operationId: `Customer.prototype.postLocationDeviceGroup`

**Required to call:** `id` (path), `locationId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `data` | body | PostLocationDeviceGroupRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Customer or location not found; `422` Invalid request; `500` Unhandled API error

#### `GET` `/Customers/{id}/locations/{locationId}/groups/{groupId}`
*Retrieve Device Group by id for location.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist and is not known to Plume. Device Group does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getLocationDeviceGroupById`

**Required to call:** `id` (path), `locationId` (path), `groupId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `groupId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/groups/{groupId}`
*Delete a Device group for a location ID.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or Group id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteLocationDeviceGroup`

**Required to call:** `id` (path), `locationId` (path), `groupId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `groupId` | path | string | **REQUIRED** |  |
| `blockUnassignedDevices` | formData | boolean | optional | block any devices previously assigned to Group (false by default) |

**Possible responses:** `204` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/groups/{groupId}`
*Update a Device Group for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist and is not known to Plume.</div>
<div><strong>422</strong>: Nickname must be defined and mac addresses must be valid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchLocationDeviceGroup`

**Required to call:** `id` (path), `locationId` (path), `groupId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `groupId` | path | string | **REQUIRED** | Device Group ID |
| `nickname` | formData | string | optional |  |
| `imageId` | formData | string | optional | unique identifier for referencing a Device group's hosted profile image, defaults to empty string |
| `assignedDevices` | formData | string | optional | mac addresses of devices assigned to this Person |
| `profile` | formData | string | optional | allowed values are: kid, teen, adult, senior, household, employee |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/groups/{groupId}/devices/{mac}`
*Unassign a device from group for a location ID.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, group id, or mac does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteDeviceFromLocationDeviceGroup`

**Required to call:** `id` (path), `locationId` (path), `groupId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `groupId` | path | string | **REQUIRED** |  |
| `mac` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/groups/{groupId}/profile`
*Delete a group's Profile for a location ID.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or group id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteLocationDeviceGroupProfile`

**Required to call:** `id` (path), `locationId` (path), `groupId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `groupId` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/groups/{groupId}/profile`
*Update a group's Profile for a location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or group id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.updateLocationDeviceGroupProfile`

**Required to call:** `id` (path), `locationId` (path), `groupId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `groupId` | path | string | **REQUIRED** |  |
| `profile` | formData | string | optional | Valid values: employee, kid, teen, adult, senior, household |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/persons`
*Get all Persons for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getPersons`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/persons`
*Create a Person for a Location ID.*

Creates a person on a specified location.

You can provide only nickname or both firstName and lastName.
Additionally you can provide an array of assigned devices that will be assigned to person, and also a primary device.
Optionally you can provide security policy config to be applied for this person.

operationId: `Customer.prototype.postPersons`

**Required to call:** `id` (path), `locationId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `data` | body | PostPersonRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/persons/{personId}`
*Get a Person by ID for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getPersonById`

**Required to call:** `id` (path), `locationId` (path), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |
| `networkId` | query | string | optional | Secondary network ID |
| `vapType` | query | string | optional | fronthaul (employee) or captivePortal (guest) |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/persons/{personId}`
*Delete a Person for a location ID.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or Person id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deletePerson`

**Required to call:** `id` (path), `locationId` (path), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |
| `blockUnassignedDevices` | formData | boolean | optional | block any devices previously assigned to Person (false by default) |

**Possible responses:** `204` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/persons/{personId}`
*Update a Person for a location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or Person id does not exist and is not known to Plume</div>
<div><strong>409</strong>: primaryDevice is not included in the list of assignedDevices[]</div>
<div><strong>422</strong>: Mac addresses must be valid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchPerson`

**Required to call:** `id` (path), `locationId` (path), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |
| `nickname` | formData | string | optional |  |
| `firstName` | formData | string | optional |  |
| `lastName` | formData | string | optional |  |
| `imageId` | formData | string | optional | unique identifier for referencing a Person's hosted profile image |
| `primaryDevice` | formData | string | optional | mac addresses of Person's primary device |
| `assignedDevices` | formData | string | optional | mac addresses assigned to this Person |
| `homeAwayNotification` | formData | boolean | optional | track person homeAway state |
| `permission` | formData | string | optional | permission object for creating or deleting the manager |
| `email` | formData | string | optional | email for sending the manager invite |
| `serviceLinking` | formData | string | optional | serviceLinking object that links this Person object to a 3rd party's Person |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/persons/{personId}/devices/{mac}`
*Unassign a device from Person for a location ID.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, Person id, or mac does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteDeviceFromPerson`

**Required to call:** `id` (path), `locationId` (path), `personId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |
| `mac` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/securityPolicy`
*Returns the security policy Device for a Location ID.*

<div><strong>200</strong>: Success, device returned.</div>
<div><strong>404</strong>: customer id or location id does not exist. Or, device not found in this network 's history.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDeviceSecurity`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** | mac of device |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/devices/{mac}/securityPolicy`
*Update a Device's Security Policy for a location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or Person id does not exist and is not known to Plume</div>
<div><strong>409</strong>: Device is assigned to a person so its security policy must be configured on the Person</div>
<div><strong>422</strong>: Mac addresses must be valid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchDeviceSecurityPolicy`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `secureAndProtect` | formData | boolean | optional |  |
| `iotProtect` | formData | boolean | optional |  |
| `iotProtectReason` | formData | string | optional |  |
| `content` | formData | string | optional | Valid values: 'kids \|\| teenagers \|\| adBlocking \|\| adultAndSensitive \|\| workAppropriate' |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/securityPolicy`
*Get a Security Policy for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getLocationSecurityPolicy`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | query | string | optional | Secondary network ID |
| `vapType` | query | string | optional | fronthaul (employee) or captivePortal (guest) |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/securityPolicy`
*Update a Location's Security Policy by location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchLocationSecurityPolicy`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `secureAndProtect` | formData | boolean | optional |  |
| `iotProtect` | formData | boolean | optional |  |
| `safeSearchMode` | formData | string | optional | valid values: auto, enable, disable |
| `disablePrivateRelayMode` | formData | string | optional | valid values: auto, enable, disable |
| `content` | formData | string | optional | Valid values: 'kids \|\| teenagers \|\| adBlocking \|\| adultAndSensitive \|\| workAppropriate' |
| `appliesToAllDevices` | formData | string | optional | hash map of security policy IDs that should be applied to all devices |
| `blockAll` | formData | boolean | optional |  |
| `networkId` | formData | string | optional | Secondary network ID to target |
| `vapType` | formData | string | optional | fronthaul (employee) or captivePortal (guest) |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/persons/{personId}/qos/appPrioritization`
*Get person status for app prioritization.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getAppPrioritizationPersonConfig`

**Required to call:** `id` (path), `locationId` (path), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `personId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/persons/{personId}/qos/appPrioritization`
*Delete person app prioritization config.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteAppPrioritizationPersonConfig`

**Required to call:** `id` (path), `locationId` (path), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `personId` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/persons/{personId}/qos/appPrioritization`
*Update person app prioritization config.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.createOrUpdateAppPrioritizationPersonConfig`

**Required to call:** `id` (path), `locationId` (path), `personId` (path), `template` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `personId` | path | string | **REQUIRED** |  |
| `template` | formData | string | **REQUIRED** | value supported - personPriority |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/qos/appPrioritization`
*Get status for app prioritization.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getAppPrioritizationLocationConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/qos/appPrioritization`
*Update app prioritization config.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchAppPrioritizationLocationConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `enabled` | formData | boolean | optional | true if app prioritization is enabled |
| `mode` | formData | string | optional | App Prioritization mode - any of auto \| enable \| disable |
| `isFirstTimeUserExperience` | formData | boolean | optional | true if it is first time user experience |
| `template` | formData | string | optional | Template for app prioritization |
| `customSettingEnabled` | formData | boolean | optional | true if custom setting is enabled |
| `customSetting` | formData | string | optional | Settings for app prioritization |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/qos/appPrioritization/customSetting`
*Set custom setting to default for app prioritization.*

operationId: `Customer.prototype.deleteAppPrioritizationLocationConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/qos/appPrioritization/monitoring`
*Get monitoring metrics for app prioritization.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getAppPrioritizationMonitoring`

**Required to call:** `id` (path), `locationId` (path), `startTime` (formData), `endTime` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `granularity` | formData | string | optional | any of the values - total/15 minutes/1 hour/1 day |
| `macs` | formData | string | optional | array of macs[] |
| `trafficClasses` | formData | string | optional | array of trafficClasses[] |
| `startTime` | formData | string | **REQUIRED** | format yyyy-mm-ddThh:MM:ss.nnnZ, 24 hours time specified in UTC |
| `endTime` | formData | string | **REQUIRED** | format yyyy-mm-ddThh:MM:ss.nnnZ, 24 hours time specified in UTC |
| `sortOrder` | formData | string | optional | TxBytes"\|\| "RxBytes |
| `limit` | formData | number | optional | Maximum number of devices to return. |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/appqoe/traffic_class_stats`
*Get App QoE metrics for traffic classes.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getAppQoeTrafficClassMetrics__get_Customers_{id}_locations_{locationId}_appqoe_traffic_class_stats`

**Required to call:** `id` (path), `locationId` (path), `granularity` (query), `startTime` (query), `endTime` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `granularity` | query | string | **REQUIRED** | any of the values - total/1 minute/15 minutes/1 hour/1 day |
| `macs` | query | string | optional | array of macs[] |
| `startTime` | query | string | **REQUIRED** | format yyyy-mm-ddThh:MM:ss.nnnZ, 24 hours time specified in UTC |
| `endTime` | query | string | **REQUIRED** | format yyyy-mm-ddThh:MM:ss.nnnZ, 24 hours time specified in UTC |
| `trafficClasses` | query | string | optional | array of trafficClasses |
| `limit` | query | number | optional | Maximum number of devices to return. |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/appqoe/traffic_class_stats`
*Get App QoE metrics for traffic classes.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getAppQoeTrafficClassMetrics__post_Customers_{id}_locations_{locationId}_appqoe_traffic_class_stats`

**Required to call:** `id` (path), `locationId` (path), `granularity` (formData), `startTime` (formData), `endTime` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `granularity` | formData | string | **REQUIRED** | any of the values - total/1 minute/15 minutes/1 hour/1 day |
| `macs` | formData | string | optional | array of macs |
| `startTime` | formData | string | **REQUIRED** | format yyyy-mm-ddThh:MM:ss.nnnZ, 24 hours time specified in UTC |
| `endTime` | formData | string | **REQUIRED** | format yyyy-mm-ddThh:MM:ss.nnnZ, 24 hours time specified in UTC |
| `trafficClasses` | formData | string | optional | array of trafficClasses |
| `limit` | formData | number | optional | Maximum number of devices to return. |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/appqoe/AppQoeStatsByTrafficClass`
*Get App QoE metrics by traffic classes / devices / apps.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getAppQoeStatsByTrafficClass`

**Required to call:** `id` (path), `locationId` (path), `timePeriod` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `timePeriod` | formData | string | **REQUIRED** | Any of "lastHour", "last24Hours","last7Days","last30Days" |
| `includeApps` | formData | boolean | optional | Default false, to include app stats in the response |
| `trafficClassNames` | formData | string | optional | array of traffic classes - default list - av_streaming, gaming, video_conferencing |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/appqoe/AppQoeStatsByTrafficClassApps`
*Get App QoE metrics by traffic classes / apps.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getAppQoeStatsByTrafficClassApps`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `timePeriod` | formData | string | optional | Any of "lastHour", "last24Hours","last7Days","last30Days" |
| `trafficClassNames` | formData | string | optional | array of traffic classes - default list - av_streaming, gaming, video_conferencing, game, video, stream |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/appqoe/AppQoeStatsByProfile`
*Get App QoE metrics by Persons / devices.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getAppQoeStatsByProfileDevices`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `timePeriod` | formData | string | optional | Any of "lastHour", "last24Hours","last7Days","last30Days" |
| `trafficClassNames` | formData | string | optional | array of traffic classes - default list - av_streaming, gaming, video_conferencing, game, video, stream |
| `persons` | formData | string | optional | array of person ids. Default all persons in location |
| `groups` | formData | string | optional | array of group ids. Default all groups in location |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/qos/appPrioritization/templateConfig`
*Get AppPrioritization template configs*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getAppPrioritizationTemplateConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/securityPolicy/hourlyBlockedCounts`
*Get a Security Policy Hourly Blocked Counts for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getLocationSecurityPolicyHourlyCounts`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/securityPolicy/hourlyBlockedCounts`
*Get a Security Policy Hourly Blocked Counts for a Device for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDeviceSecurityPolicyHourlyCounts`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** | mac of device |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/persons/{personId}/securityPolicy/hourlyBlockedCounts`
*Get a Security Policy Hourly Blocked Counts for a Person for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getPersonSecurityPolicyHourlyCounts`

**Required to call:** `id` (path), `locationId` (path), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** | person |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/groupOfUnassignedDevices/securityPolicy/hourlyBlockedCounts`
*Get a Security Policy Hourly Blocked Counts for group Of Unassigned Devices for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getGroupOfUnassignedDevicesSecurityPolicyHourlyCounts`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/securityPolicy/events`
*Get a Security Policy Events for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getLocationSecurityPolicyEvents`

**Required to call:** `id` (path), `locationId` (path), `startTime` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `includes` | query | string | optional |  |
| `startTime` | query | string | **REQUIRED** |  |
| `limit` | query | number | optional |  |
| `direction` | query | string | optional |  |
| `protectionType` | query | string | optional |  |
| `showOnlyIot` | query | boolean | optional |  |
| `showAlsoIot` | query | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/securityPolicy/events`
*Delete a Location's Security Events history for a location ID.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, Device or DNS does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteLocationEventsHistory`

**Required to call:** `id` (path), `locationId` (path), `categories` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `categories` | formData | string | **REQUIRED** |  |
| `reason` | formData | string | optional |  |

**Possible responses:** `204` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/securityPolicy/guard/events`
*Get the Guard Event Domain Groups for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getLocationGuardEventsTldOrIp`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `macs` | formData | string | optional | array of macs[] |
| `persons` | formData | string | optional | array of personIds[] |
| `groups` | formData | string | optional | array of groupIds[] |
| `tldOrIp` | formData | string | optional | top level domain or IP address |
| `protectionType` | formData | string | optional | filter by protectionType: ihp \| ohp. Returns all types by default. |
| `eventTypes` | formData | string | optional | filter by event type, any combo of: 'adBlocking','teenagers','kids','adultAndSensitive','secureAndProtect','ipThreatOutbound','ipThreatInbound', 'iotProtect'. Returns all types by default. |
| `timePeriod` | formData | string | optional | Any of "last24Hours", "last7Days", "last30Days" |
| `groupOfUnassignedDevices` | formData | boolean | optional | to include the group of unassigned devices |
| `includeBlocklistEvents` | formData | boolean | optional | include block events from blocklisted domains |
| `includeAppEvents` | formData | boolean | optional | include App blocking events |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/securityPolicy/guard/groupEventsSummary`
*Get the Guard Event Stats for all groups in a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getLocationGuardLocationDeviceGroupEventsSummary`

**Required to call:** `id` (path), `locationId` (path), `timePeriod` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `timePeriod` | query | string | **REQUIRED** | Any of "last24Hours","last7Days","last30Days" |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/securityPolicy/guard/personEventsSummary`
*Get the Guard Event Stats for all persons in a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getLocationGuardPersonEventsSummary`

**Required to call:** `id` (path), `locationId` (path), `timePeriod` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `timePeriod` | query | string | **REQUIRED** | Any of "last24Hours","last7Days","last30Days" |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/securityPolicy/guard/eventStats`
*Get the Guard Event Stats for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getLocationGuardEventStats`

**Required to call:** `id` (path), `locationId` (path), `timePeriod` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `macs` | formData | string | optional | array of macs[] |
| `persons` | formData | string | optional | array of personIds[] |
| `groups` | formData | string | optional | array of groupIds[] |
| `protectionType` | formData | string | optional | filter by protectionType: ihp \| ohp. Returns all types by default. |
| `eventTypes` | formData | string | optional | filter by event type, any combo of: 'adBlocking','teenagers','kids','adultAndSensitive','secureAndProtect','ipThreatOutbound','ipThreatInbound', 'iotProtect'. Returns all types by default. |
| `timePeriod` | formData | string | **REQUIRED** | Any of "last24Hours","last7Days","last30Days" |
| `groupOfUnassignedDevices` | formData | boolean | optional | to include the group of unassigned devices |
| `includeBlocklistEvents` | formData | boolean | optional | include block events from blocklisted domains |
| `includeAppEvents` | formData | boolean | optional | include App blocking events |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/securityPolicy/events`
*Get a Security Policy Events for Device for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDeviceSecurityPolicyEvents`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `startTime` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** | mac of device |
| `includes` | query | string | optional |  |
| `startTime` | query | string | **REQUIRED** |  |
| `limit` | query | number | optional |  |
| `direction` | query | string | optional |  |
| `protectionType` | query | string | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/persons/{personId}/securityPolicy/events`
*Get a Security Policy Events for Person for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getPersonSecurityPolicyEvents`

**Required to call:** `id` (path), `locationId` (path), `personId` (path), `startTime` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** | person |
| `includes` | query | string | optional |  |
| `startTime` | query | string | **REQUIRED** |  |
| `limit` | query | number | optional |  |
| `direction` | query | string | optional |  |
| `protectionType` | query | string | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/groupOfUnassignedDevices/securityPolicy/events`
*Get a Security Policy Events for groupOfUnassignedDevices for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getGroupOfUnassignedDevicesSecurityPolicyEvents`

**Required to call:** `id` (path), `locationId` (path), `startTime` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `includes` | query | string | optional |  |
| `startTime` | query | string | **REQUIRED** |  |
| `limit` | query | number | optional |  |
| `direction` | query | string | optional |  |
| `protectionType` | query | string | optional |  |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/securityPolicy/bulk`
*Update a Location's Security Policy by location ID.*

<div><strong>202</strong>: Accepted</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.updateMultipleLocationSecurityPolicies`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `persons` | formData | string | optional | Example: [{ "id": "personId", "securityPolicy": {"secureAndProtect": true, "iotProtect": false, "adBlocking": true } }] |
| `groups` | formData | string | optional | Example: [{ "id": "groupId", "securityPolicy": {"secureAndProtect": true, "iotProtect": false, "adBlocking": true } }] |
| `groupOfUnassignedDevices` | formData | string | optional | Example: {"secureAndProtect": true, "iotProtect": true, "adBlocking": true} |

**Possible responses:** `202` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/groupOfUnassignedDevices/securityPolicy`
*Get a Security Policy for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getGroupOfUnassignedDevicesSecurityPolicy`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/groupOfUnassignedDevices/securityPolicy`
*Update a Location's Default Device Group Security Policy by location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchGroupOfUnassignedDevicesSecurityPolicy`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `secureAndProtect` | formData | boolean | optional |  |
| `iotProtect` | formData | boolean | optional |  |
| `content` | formData | string | optional | Valid values: 'kids \|\| teenagers \|\| adBlocking \|\| adultAndSensitive \|\| workAppropriate' |

**Possible responses:** `202` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/securityPolicy/websites/whitelist`
*Update a Location's Security Policy for a location ID to include a whitelisted DNS entry.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or Device does not exist and is not known to Plume</div>
<div><strong>422</strong>: DNS value is invalid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postLocationSecurityPolicyWebsitesWhitelist`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `dns` | formData | string | optional |  |
| `type` | formData | string | optional |  |
| `value` | formData | string | optional |  |
| `direction` | formData | string | optional |  |
| `geoLocation` | formData | string | optional |  |
| `eventType` | formData | string | optional | EventType field from events response - can be 'kids', 'teenagers', 'secureAndProtect', etc |
| `source` | formData | string | optional | Source field from events response - can be 'brightcloud', 'webpulse', 'gatekeeper', 'gatekeeper-ohp' |
| `endTimestamp` | formData | number | optional | the end time stamp,  UTC unix epoch timestamp in ms |
| `akamaiCategoryId` | formData | number | optional | the akamai category id, number |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/securityPolicy/wildcardWebsites/whitelist`
*Update a Location's Security Policy for a location ID to include a wildcard whitelisted DNS entry.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or Device does not exist and is not known to Plume</div>
<div><strong>422</strong>: DNS value is invalid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postLocationSecurityPolicyWildcardWebsitesWhitelist`

**Required to call:** `id` (path), `locationId` (path), `dns` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `dns` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/securityPolicy/websites/whitelist/approvalRequests`
*Get a list of pending approval requests for this location.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, CustomerId or requst id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getWhitelistApprovalRequests`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/securityPolicy/websites/whitelist/approvalRequests`
*Post a request for a whitelist exception to be added to your person profile.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, CustomerId or requst id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postWhitelistApprovalRequest`

**Required to call:** `id` (path), `locationId` (path), `value` (formData), `type` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `value` | formData | string | **REQUIRED** |  |
| `type` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/securityPolicy/websites/whitelist/approvalRequests/{requestId}`
*Approve a persons whitelist request and add it to the security policy.*

<div><strong>204</strong>: No content.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, CustomerId or requst id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.approveWhitelistRequest`

**Required to call:** `id` (path), `locationId` (path), `requestId` (path), `persons` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `requestId` | path | string | **REQUIRED** |  |
| `persons` | formData | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/securityPolicy/websites/whitelist/approvalRequests/{requestId}`
*Reject an approval request for a website whitelist*

<div><strong>204</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, CustomerId or requst id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.rejectWhitelistRequest`

**Required to call:** `id` (path), `locationId` (path), `requestId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `requestId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/securityPolicy/websites/whitelist/{dns}`
*Update a Locations's Security Policy for a location ID to remove a whitelisted DNS entry.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or DNS does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteFromLocationSecurityPolicyWebsitesWhitelist`

**Required to call:** `id` (path), `locationId` (path), `dns` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `dns` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/securityPolicy/wildcardWebsites/whitelist/{dns}`
*Update a Locations's Security Policy for a location ID to remove a wildcard whitelisted DNS entry.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or DNS does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteFromLocationSecurityPolicyWildcardWebsitesWhitelist`

**Required to call:** `id` (path), `locationId` (path), `dns` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `dns` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/securityPolicy/websites/blacklist`
*Update a Location's Security Policy for a location ID to include a blacklisted DNS entry.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or Device does not exist and is not known to Plume</div>
<div><strong>422</strong>: DNS value is invalid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postLocationSecurityPolicyWebsitesBlacklist`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `dns` | formData | string | optional |  |
| `type` | formData | string | optional |  |
| `value` | formData | string | optional |  |
| `direction` | formData | string | optional |  |
| `geoLocation` | formData | string | optional |  |
| `endTimestamp` | formData | number | optional | the end time stamp,  UTC unix epoch timestamp in ms |
| `akamaiCategoryId` | formData | number | optional | the akamai category id, number |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/securityPolicy/websites/blacklist/{dns}`
*Update a Location's Security Policy for a location ID to remove a blacklisted DNS entry.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or DNS does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteFromLocationSecurityPolicyWebsitesBlacklist`

**Required to call:** `id` (path), `locationId` (path), `dns` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `dns` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/groupOfUnassignedDevices/securityPolicy/websites/whitelist`
*Update a Location's Default Device Group Security Policy for a location ID to include a whitelisted DNS entry.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or Device does not exist and is not known to Plume</div>
<div><strong>422</strong>: DNS value is invalid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postGroupOfUnassignedDevicesSecurityPolicyWebsitesWhitelist`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `dns` | formData | string | optional |  |
| `type` | formData | string | optional |  |
| `value` | formData | string | optional |  |
| `direction` | formData | string | optional |  |
| `geoLocation` | formData | string | optional |  |
| `endTimestamp` | formData | number | optional | the end time stamp,  UTC unix epoch timestamp in ms |
| `akamaiCategoryId` | formData | number | optional | the akamai category id, number |

**Possible responses:** `202` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/groupOfUnassignedDevices/securityPolicy/websites/whitelist/{dns}`
*Update a Location's Default Device Group Security Policy for a location ID to remove a whitelisted DNS entry.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or DNS does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteFromGroupOfUnassignedDevicesSecurityPolicyWebsitesWhitelist`

**Required to call:** `id` (path), `locationId` (path), `dns` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `dns` | path | string | **REQUIRED** |  |

**Possible responses:** `202` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/groupOfUnassignedDevices/securityPolicy/websites/blacklist`
*Update a Location's Default Device Group Security Policy for a location ID to include a blacklisted DNS entry.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or Device does not exist and is not known to Plume</div>
<div><strong>422</strong>: DNS value is invalid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postGroupOfUnassignedDevicesSecurityPolicyWebsitesBlacklist`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `dns` | formData | string | optional |  |
| `type` | formData | string | optional |  |
| `value` | formData | string | optional |  |
| `direction` | formData | string | optional |  |
| `geoLocation` | formData | string | optional |  |
| `endTimestamp` | formData | number | optional | the end time stamp,  UTC unix epoch timestamp in ms |
| `akamaiCategoryId` | formData | number | optional | the akamai category id, number |

**Possible responses:** `202` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/groupOfUnassignedDevices/securityPolicy/websites/blacklist/{dns}`
*Update a Location's Default Device Group Security Policy for a location ID to remove a blacklisted DNS entry.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or DNS does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteFromGroupOfUnassignedDevicesSecurityPolicyWebsitesBlacklist`

**Required to call:** `id` (path), `locationId` (path), `dns` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `dns` | path | string | **REQUIRED** |  |

**Possible responses:** `202` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/devices/{mac}/securityPolicy/anomaly/websites/whitelist`
*Approve a previously blacklisted anomalous dns for a Device on a location.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>422</strong>: DNS value is invalid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postDeviceSecurityPolicyAnomalyWhitelist`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `fqdn` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `fqdn` | formData | string | **REQUIRED** |  |
| `reason` | formData | string | optional |  |
| `ttl` | formData | number | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/devices/{mac}/securityPolicy/anomaly/websites/whitelist/{fqdn}`
*Update a Location's Anomaly Security Policy for a location ID to remove a whitelisted DNS entry.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, Device or DNS does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteDeviceSecurityPolicyAnomalyWhitelist`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `fqdn` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `fqdn` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/devices/{mac}/securityPolicy/anomaly/experience`
*Initiate an Anomaly Experience (demo) for a Device on a location.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postDeviceSecurityPolicyAnomalyExperience`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `fqdn` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `fqdn` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/devices/{mac}/securityPolicy/anomaly/experience`
*Delete an Anomaly Experience (demo) for a Device on a location.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, Device does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteDeviceSecurityPolicyAnomalyExperience`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/securityPolicy/ohp/deviceSetup`
*Setup a Mobile Device for Security Out of Home Protection (returns a Deeplink for use with Mobolize).*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postLocationSecurityPolicyOHPDeviceSetup`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `lanIpv4` | formData | string | optional | Mobile device lanIpv4 address, if any |
| `lanIpv6` | formData | string | optional | Mobile device lanIpv6 address, if any |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/securityPolicy/ohp/deviceUuid`
*Update the Device UUID Mapping for Out of Home Protection.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putLocationSecurityPolicyOHPDeviceUuidMapping`

**Required to call:** `id` (path), `locationId` (path), `uuid` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `lanIpv4` | formData | string | optional | Mobile device lanIpv4 address, if any |
| `lanIpv6` | formData | string | optional | Mobile device lanIpv6 address, if any |
| `deviceId` | formData | string | optional | Internal device-id |
| `uuid` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/securityPolicy/ohp/register`
*Setup a Mobile Device for Security Out of Home Protection (returns a Deeplink for use with Mobolize).*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postLocationSecurityPolicyOHPRegister`

**Required to call:** `id` (path), `locationId` (path), `os` (formData), `device` (formData), `software_version` (formData), `mmc_agent_guid` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `os` | formData | string | **REQUIRED** | Mobile device os |
| `device` | formData | string | **REQUIRED** | Mobile device name |
| `software_version` | formData | string | **REQUIRED** | Mobile software version |
| `mmc_agent_guid` | formData | string | **REQUIRED** | Mobile mac agent guid |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/devices/{mac}/securityPolicy/ohp`
*Update the Device UUID Mapping for Out of Home Protection.*

<div><strong>204</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or Device does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchDeviceOHPConfiguration`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `OHPNotificationsFlags` | formData | string | optional | OHP feature flags |
| `disableMobilizeSdk` | formData | boolean | optional | enable or disable OHP SDK on the device |

**Possible responses:** `204` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/securityPolicy/ohp/protectionState`
*Update the Device Protection State for Out of Home Protection.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putLocationSecurityPolicyOHPProtectionState`

**Required to call:** `id` (path), `locationId` (path), `uuid` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `uuid` | formData | string | **REQUIRED** | Mobile device uuid (as was assigned by Mobolize) |
| `protectionState` | formData | string | optional | ProtectionState info as obtained directly from the Mobolize SDK, null if deleting ProtectionState |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/devices/{mac}/securityPolicy/remoteConnections/allow`
*Post a Remote Connection Allow IpAddress/ttl for the given device and Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or Device mac does not exist and is not known to Plume</div>
<div><strong>422</strong>: Fields have an invalid type or value.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postRemoteConnectionsAllow`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `type` (formData), `value` (formData), `expiresAt` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `type` | formData | string | **REQUIRED** | either ipv4 or ipv6 |
| `value` | formData | string | **REQUIRED** | ipaddress |
| `expiresAt` | formData | string | **REQUIRED** | UTC timestamp in ISO 8601 format |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/devices/{mac}/securityPolicy/remoteConnections/allow/{ipaddr}`
*Delete a Remote Connection Allow IpAddress/ttl for the given device and Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or Device mac does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteRemoteConnectionsAllow`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `ipaddr` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `ipaddr` | path | string | **REQUIRED** | ipaddress |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/devices/{mac}/securityPolicy/remoteConnections/allowAll`
*Post a Remote Connection Allow All/ttl for the given device and Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or Device mac does not exist and is not known to Plume</div>
<div><strong>422</strong>: Fields have an invalid type or value.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postRemoteConnectionsAllowAll`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `expiresAt` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `expiresAt` | formData | string | **REQUIRED** | UTC timestamp in ISO 8601 format |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/devices/{mac}/securityPolicy/remoteConnections/allowAll`
*Delete a Remote Connection Allow All for the given device and Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or Device mac does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteRemoteConnectionsAllowAll`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/securityPolicy/remoteConnections`
*Get the Unauthorized Remote Connections config for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getRemoteConnectionsConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/securityPolicy/remoteConnections`
*Patch a Remote Connections Config for the given Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchRemoteConnectionsConfig`

**Required to call:** `id` (path), `locationId` (path), `mode` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mode` | formData | string | **REQUIRED** | Any of "auto", "enabled", "disabled", "highRiskOnly" |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/persons/{personId}/securityPolicy`
*Update a Person's Security Policy for a location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or Person id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchPersonSecurityPolicy`

**Required to call:** `id` (path), `locationId` (path), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |
| `secureAndProtect` | formData | boolean | optional |  |
| `iotProtect` | formData | boolean | optional |  |
| `safeSearchMode` | formData | string | optional | valid values: auto, enable, disable |
| `disablePrivateRelayMode` | formData | string | optional | valid values: auto, enable, disable |
| `content` | formData | string | optional | Valid values: 'kids \|\| teenagers \|\| adBlocking \|\| adultAndSensitive \|\| workAppropriate' |
| `networkId` | formData | string | optional | Secondary network ID to target |
| `vapType` | formData | string | optional | fronthaul (employee) or captivePortal (guest) |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/groups/{groupId}/securityPolicy`
*Retrieve group's Security Policy for a location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or Group id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getLocationDeviceGroupSecurityPolicy`

**Required to call:** `id` (path), `locationId` (path), `groupId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `groupId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/groups/{groupId}/securityPolicy`
*Update a group's Security Policy for a location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or Group id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchLocationDeviceGroupSecurityPolicy`

**Required to call:** `id` (path), `locationId` (path), `groupId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `groupId` | path | string | **REQUIRED** |  |
| `secureAndProtect` | formData | boolean | optional |  |
| `iotProtect` | formData | boolean | optional |  |
| `safeSearchMode` | formData | string | optional | valid values: auto, enable, disable |
| `disablePrivateRelayMode` | formData | string | optional | valid values: auto, enable, disable |
| `content` | formData | string | optional | Valid values: 'kids \|\| teenagers \|\| adBlocking \|\| adultAndSensitive \|\| workAppropriate' |
| `networkId` | formData | string | optional | Secondary network ID to target |
| `vapType` | formData | string | optional | fronthaul (employee) or captivePortal (guest) |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/persons/{personId}/profile`
*Delete a Person's Profile for a location ID.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or Person id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deletePersonProfile`

**Required to call:** `id` (path), `locationId` (path), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/persons/{personId}/profile`
*Update a Person's Profile for a location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or Person id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchPersonProfile`

**Required to call:** `id` (path), `locationId` (path), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |
| `type` | formData | string | optional | Valid values: 'employee' |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/groups/{groupId}/securityPolicy/websites/whitelist`
*Update a device group's Security Policy for a location ID to include a whitelisted DNS entry.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or device group id does not exist and is not known to Plume</div>
<div><strong>422</strong>: DNS value is invalid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postLocationDeviceGroupSecurityPolicyWebsitesWhitelist`

**Required to call:** `id` (path), `locationId` (path), `groupId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `groupId` | path | string | **REQUIRED** |  |
| `dns` | formData | string | optional |  |
| `type` | formData | string | optional |  |
| `value` | formData | string | optional |  |
| `direction` | formData | string | optional |  |
| `geoLocation` | formData | string | optional |  |
| `eventType` | formData | string | optional | EventType field from events response - can be 'kids', 'teenagers', 'secureAndProtect', etc |
| `source` | formData | string | optional | Source field from events response - can be 'brightcloud', 'webpulse', 'gatekeeper', 'gatekeeper-ohp' |
| `endTimestamp` | formData | number | optional | the end time stamp,  UTC unix epoch timestamp in ms |
| `akamaiCategoryId` | formData | number | optional | the akamai category id, number |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/groups/{groupId}/securityPolicy/websites/whitelist/{dns}`
*Update a device group's Security Policy for a location ID to remove a whitelisted DNS entry.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, group id, or DNS does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteFromLocationDeviceGroupSecurityPolicyWebsitesWhitelist`

**Required to call:** `id` (path), `locationId` (path), `groupId` (path), `dns` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `groupId` | path | string | **REQUIRED** |  |
| `dns` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/groups/{groupId}/securityPolicy/websites/blacklist`
*Update a device group's Security Policy for a location ID to include a blacklisted DNS entry.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or group id does not exist and is not known to Plume</div>
<div><strong>422</strong>: DNS value is invalid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postLocationDeviceGroupSecurityPolicyWebsitesBlacklist`

**Required to call:** `id` (path), `locationId` (path), `groupId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `groupId` | path | string | **REQUIRED** |  |
| `dns` | formData | string | optional |  |
| `type` | formData | string | optional |  |
| `value` | formData | string | optional |  |
| `direction` | formData | string | optional |  |
| `geoLocation` | formData | string | optional |  |
| `endTimestamp` | formData | number | optional | the end time stamp,  UTC unix epoch timestamp in ms |
| `akamaiCategoryId` | formData | number | optional | the akamai category id, number |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/groups/{groupId}/securityPolicy/websites/blacklist/{dns}`
*Update a Person's Security Policy for a location ID to remove a blacklisted DNS entry.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, Person id, or DNS does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteFromLocationDeviceGroupSecurityPolicyWebsitesBlacklist`

**Required to call:** `id` (path), `locationId` (path), `groupId` (path), `dns` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `groupId` | path | string | **REQUIRED** |  |
| `dns` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/persons/{personId}/securityPolicy/websites/whitelist`
*Update a Person's Security Policy for a location ID to include a whitelisted DNS entry.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or Person id does not exist and is not known to Plume</div>
<div><strong>422</strong>: DNS value is invalid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postPersonSecurityPolicyWebsitesWhitelist`

**Required to call:** `id` (path), `locationId` (path), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |
| `dns` | formData | string | optional |  |
| `type` | formData | string | optional |  |
| `value` | formData | string | optional |  |
| `direction` | formData | string | optional |  |
| `geoLocation` | formData | string | optional |  |
| `eventType` | formData | string | optional | EventType field from events response - can be 'kids', 'teenagers', 'secureAndProtect', etc |
| `source` | formData | string | optional | Source field from events response - can be 'brightcloud', 'webpulse', 'gatekeeper', 'gatekeeper-ohp' |
| `endTimestamp` | formData | number | optional | the end time stamp,  UTC unix epoch timestamp in ms |
| `akamaiCategoryId` | formData | number | optional | the akamai category id, number |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/persons/{personId}/securityPolicy/websites/whitelist/{dns}`
*Update a Person's Security Policy for a location ID to remove a whitelisted DNS entry.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, Person id, or DNS does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteFromPersonSecurityPolicyWebsitesWhitelist`

**Required to call:** `id` (path), `locationId` (path), `personId` (path), `dns` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |
| `dns` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/persons/{personId}/securityPolicy/websites/blacklist`
*Update a Person's Security Policy for a location ID to include a blacklisted DNS entry.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or Person id does not exist and is not known to Plume</div>
<div><strong>422</strong>: DNS value is invalid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postPersonSecurityPolicyWebsitesBlacklist`

**Required to call:** `id` (path), `locationId` (path), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |
| `dns` | formData | string | optional |  |
| `type` | formData | string | optional |  |
| `value` | formData | string | optional |  |
| `direction` | formData | string | optional |  |
| `geoLocation` | formData | string | optional |  |
| `endTimestamp` | formData | number | optional | the end time stamp,  UTC unix epoch timestamp in ms |
| `akamaiCategoryId` | formData | number | optional | the akamai category id, number |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/persons/{personId}/securityPolicy/websites/blacklist/{dns}`
*Update a Person's Security Policy for a location ID to remove a blacklisted DNS entry.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, Person id, or DNS does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteFromPersonSecurityPolicyWebsitesBlacklist`

**Required to call:** `id` (path), `locationId` (path), `personId` (path), `dns` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |
| `dns` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/devices/{mac}/securityPolicy/websites/whitelist`
*Update a Device's Security Policy for a location ID to include a whitelisted DNS entry.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or Device does not exist and is not known to Plume</div>
<div><strong>422</strong>: DNS value is invalid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postDeviceSecurityPolicyWebsitesWhitelist`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `dns` | formData | string | optional |  |
| `type` | formData | string | optional |  |
| `value` | formData | string | optional |  |
| `direction` | formData | string | optional |  |
| `geoLocation` | formData | string | optional |  |
| `eventType` | formData | string | optional | EventType field from event response - can be 'kids', 'teenagers', 'secureAndProtect, etc' |
| `source` | formData | string | optional | Source field from events response - can be 'brightcloud', 'webpulse', 'gatekeeper', 'gatekeeper-ohp' |
| `endTimestamp` | formData | number | optional | the end time stamp,  UTC unix epoch timestamp in ms |
| `akamaiCategoryId` | formData | number | optional | the akamai category id, number |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/devices/{mac}/securityPolicy/websites/whitelist/{dns}`
*Update a Device's Security Policy for a location ID to remove a whitelisted DNS entry.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, Device, or DNS does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteFromDeviceSecurityPolicyWebsitesWhitelist`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `dns` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `dns` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/devices/{mac}/securityPolicy/websites/blacklist`
*Update a Device's Security Policy for a location ID to include a blacklisted DNS entry.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or Device does not exist and is not known to Plume</div>
<div><strong>422</strong>: DNS value is invalid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postDeviceSecurityPolicyWebsitesBlacklist`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `dns` | formData | string | optional |  |
| `type` | formData | string | optional |  |
| `value` | formData | string | optional |  |
| `direction` | formData | string | optional |  |
| `geoLocation` | formData | string | optional |  |
| `endTimestamp` | formData | number | optional | the end time stamp,  UTC unix epoch timestamp in ms |
| `akamaiCategoryId` | formData | number | optional | the akamai category id, number |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/devices/{mac}/securityPolicy/websites/blacklist/{dns}`
*Update a Device's Security Policy for a location ID to remove a blacklisted DNS entry.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, Device, or DNS does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteFromDeviceSecurityPolicyWebsitesBlacklist`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `dns` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `dns` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/configAudit/events`
*Get a Config Audit Trail Events for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getLocationConfigAuditEvents`

**Required to call:** `id` (path), `locationId` (path), `includes` (query), `startTime` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `includes` | query | string | **REQUIRED** |  |
| `startTime` | query | string | **REQUIRED** |  |
| `limit` | query | number | optional |  |
| `direction` | query | string | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/appFacade/wifiDashboard`
*WiFi Dashboard*

<div><strong>200</strong>: Success, response object returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getWifiDashboard`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/devices/{mac}`
*Nickname a Customer's device for all locations.*

<div><strong>200</strong>: Success, device name has been updated<br/>but not validated as a device that <br/>has ever connected.</div>
<div><strong>400</strong>: nickname value must be defined.</div>
<div><strong>404</strong>: customer id and/or mac does not exist.</div>
<div><strong>422</strong>: nickname value must be less than 33 characters.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putDeviceNickname`

**Required to call:** `id` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `mac` | path | string | **REQUIRED** |  |
| `nickname` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/devices/{mac}/forcedSteer`
*Force a device to use the 2.4Ghz band with auto expire.*

<div><strong>204</strong>: Success, forced steer enabled.</div>
<div><strong>404</strong>: Location ID or Device mac not found or the device has not been online in the last 31 days</div>
<div><strong>422</strong>: expiresAt is outside of the expected range 5 to 60 minutes in the future</div>
<div><strong>422</strong>: expiresAt is an invalid UTC date</div>
<div><strong>422</strong>: expiresAt cannot be in the past</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.setForcedSteer`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** | MAC address of the target device. Must have been online in the last 31 days. |
| `expiresAt` | formData | string | optional | time of expiration in RFC 3339 format (e.g. 2021-11-24T09:13:33+00:00), must be between 5 and 60 minutes in the future. |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/devices/{mac}/forcedSteer`
*Disable 2.4Ghz band enforcement early.*

<div><strong>204</strong>: Success, forced steer ended early.</div>
<div><strong>404</strong>: Location ID or Device mac not found or the device has not been online in the last 31 days</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteForcedSteer`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** | MAC address of the target device. Must have been online in the last 31 days. |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/devices/{mac}/customType`
*Update a Customer's device type configuration (user feedback).*

<div><strong>200</strong>: Success, device type has been updated<br/>but not validated as a device that <br/>has ever connected.</div>
<div><strong>400</strong>: nickname value must be defined.</div>
<div><strong>404</strong>: customer id and/or mac does not exist.</div>
<div><strong>422</strong>: nickname value must be less than 33 characters.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchCustomDeviceType`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `category` | formData | string | optional |  |
| `brand` | formData | string | optional |  |
| `model` | formData | string | optional |  |
| `osName` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/wifiNetwork`
*Get the current WiFi SSID and PSK for a Location ID.*

<div><strong>200</strong>: Success, current Wifi Network returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or WifiNetwork does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getWifiNetwork`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/wifiNetwork`
*Set a WiFi SSID and PSK for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist and is not known to Plume</div>
<div><strong>409</strong>: A WifiNetwork already exists for this location.</div>
<div><strong>422</strong>: encryptionKey or ssid must be defined, or key length &lt; 8.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postWifiNetwork`

**Required to call:** `id` (path), `locationId` (path), `encryptionKey` (formData), `ssid` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `encryptionKey` | formData | string | **REQUIRED** | Needs to be a minimum of 8 characters |
| `ssid` | formData | string | **REQUIRED** |  |
| `wpaMode` | formData | string | optional | psk-mixed (WPA+WPA2) \|\| sae-mixed (WPA2+WPA3) \|\| psk2 (WPA2 only) \|\| sae (WPA3 only) \|\| sae-compat (WPA2+WPA3) \|\| sae-compat-relaxed (WPA2+WPA3) |
| `wpaModes` | formData | string | optional | Object with { freqBand24: wpaMode, freqBand5: wpaMode, freqBand6: sae } interface. For possible wpaMode values look at the wpaMode property. |
| `ssidBroadcast` | formData | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/wifiNetwork`
*Update the WiFi SSID and PSK for a Location ID.*

<div><strong>200</strong>: Success, your new info looks good.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id, or wifi network does not exist.</div>
<div><strong>422</strong>: encryptionKey or ssid must be defined.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putWifiNetwork`

**Required to call:** `id` (path), `locationId` (path), `encryptionKey` (formData), `ssid` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `encryptionKey` | formData | string | **REQUIRED** | Needs to be a minimum of 8 characters |
| `ssid` | formData | string | **REQUIRED** |  |
| `wpaMode` | formData | string | optional | psk-mixed (WPA+WPA2) \|\| sae-mixed (WPA2+WPA3) \|\| psk2 (WPA2 only) \|\| sae (WPA3 only) \|\| sae-compat (WPA2+WPA3) \|\| sae-compat-relaxed (WPA2+WPA3) |
| `wpaModes` | formData | string | optional | Object with { freqBand24: wpaMode, freqBand5: wpaMode, freqBand6: sae } interface. For possible wpaMode values look at the wpaMode property. |
| `ssidBroadcast` | formData | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/wifiNetwork`
*Update WiFi network configuration for a Location ID.*

<div><strong>200</strong>: Success, access zone returned</div>
<div><strong>400</strong>: Required fields missing</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Customer id, location id, or WifiNetwork does not exist</div>
<div><strong>422</strong>: Validation failed</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchWifiNetwork`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `ssid` | formData | string | optional |  |
| `uapsd` | formData | boolean | optional |  |
| `groupRekey` | formData | string | optional | auto \|\| enable \|\| disable |
| `fastTransition` | formData | string | optional | auto \|\| enable \|\| disable |
| `minWifiMode24` | formData | string | optional | auto \|\| 11a \|\| 11b \|\| 11g \|\| 11n \|\| 11ac \|\| 11ax \|\| 11b-high |
| `privateMode` | formData | boolean | optional | Stop collecting user info like DNS-Queries, UserAgent etc |
| `enabled` | formData | boolean | optional | enabled:true for active WiFi radios, enabled:false to turn `off` all WiFi radios |
| `disableDefaultServiceNetwork` | formData | boolean | optional | disables the primary network VAP |
| `wpaMode` | formData | string | optional | psk-mixed (WPA+WPA2) \|\| sae-mixed (WPA2+WPA3) \|\| psk2 (WPA2 only) \|\| sae (WPA3 only) \|\| sae-compat (WPA2+WPA3) \|\| sae-compat-relaxed (WPA2+WPA3) |
| `wpaModes` | formData | string | optional | Object with { freqBand24: wpaMode, freqBand5: wpaMode, freqBand6: sae } interface. For possible wpaMode values look at the wpaMode property. |
| `allowMlo` | formData | string | optional | auto \|\| enable \|\| disable |
| `ssidBroadcast` | formData | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/wifiNetwork/accessZones/{accessZone}/keys`
*Create a new WiFi Password*

<div><strong>200</strong>: Success, all passwords returned</div>
<div><strong>400</strong>: Required fields missing</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Customer id, location id, or WifiNetwork does not exist</div>
<div><strong>422</strong>: Password validation failed</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postWifiKey`

**Required to call:** `id` (path), `locationId` (path), `accessZone` (path), `encryptionKey` (formData), `enable` (formData), `format` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `accessZone` | path | string | **REQUIRED** | home \| guests \| internetAccessOnly |
| `encryptionKey` | formData | string | **REQUIRED** |  |
| `enable` | formData | boolean | **REQUIRED** | devices can connect using this encryptionKey |
| `format` | formData | string | **REQUIRED** | encryptionKey \| phoneNumber |
| `expiresAt` | formData | string | optional | UTC in ISO 8601 String format |
| `content` | formData | string | optional | Valid values: 'adultAndSensitive' |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/wifiNetwork/accessZones/{accessZone}/keys/{keyId}`
*Update a WiFi Password*

<div><strong>200</strong>: Success, all passwords returned</div>
<div><strong>400</strong>: Required fields missing</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Customer id, location id, or WifiNetwork does not exist</div>
<div><strong>405</strong>: Cannot disable a read-only key</div>
<div><strong>422</strong>: Password validation failed</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putWifiKey`

**Required to call:** `id` (path), `locationId` (path), `accessZone` (path), `keyId` (path), `encryptionKey` (formData), `enable` (formData), `format` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `accessZone` | path | string | **REQUIRED** | home \| guests \| internetAccessOnly |
| `keyId` | path | number | **REQUIRED** | Unique password id: 0-9 |
| `encryptionKey` | formData | string | **REQUIRED** |  |
| `enable` | formData | boolean | **REQUIRED** | devices can connect using this encryptionKey |
| `format` | formData | string | **REQUIRED** | encryptionKey \| phoneNumber |
| `expiresAt` | formData | string | optional | UTC in ISO 8601 String format |
| `content` | formData | string | optional | Valid values: 'adultAndSensitive' |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/wifiNetwork/accessZones/{accessZone}/keys/{keyId}`
*Delete a WiFi Password*

<div><strong>200</strong>: Success, all passwords returned</div>
<div><strong>400</strong>: Required fields missing</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Customer id, location id, or WifiNetwork does not exist</div>
<div><strong>405</strong>: Cannot delete a read-only key</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteWifiKey`

**Required to call:** `id` (path), `locationId` (path), `accessZone` (path), `keyId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `accessZone` | path | string | **REQUIRED** | home \| guests \| internetAccessOnly |
| `keyId` | path | number | **REQUIRED** | Unique password id: 0-9 |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/wifiNetwork/accessZones/home/devicesVisibleToGuests`
*DEPRECATED: Update home devices visible to guests.*

<div><strong>200</strong>: Success, devicesVisibleToGuests returned.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Customer id, location id, or WifiNetwork does not exist.</div>
<div><strong>422</strong>: Device mac validation failed.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putDevicesVisibleToGuests`

**Required to call:** `id` (path), `locationId` (path), `devicesVisibleToGuests` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `devicesVisibleToGuests` | formData | string | **REQUIRED** | array of macs[] |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/wifiNetwork/accessZones/home/devicesVisibleToGuests/{mac}`
*DEPRECATED: Update home devices visible to guests.*

<div><strong>200</strong>: Success, devicesVisibleToGuests returned.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Customer id, location id, or WifiNetwork does not exist.</div>
<div><strong>422</strong>: Device mac validation failed.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.addDeviceVisibleToGuests`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** | mac to be added |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/wifiNetwork/accessZones/home/devicesVisibleToGuests/{mac}`
*DEPRECATED: Update home devices visible to guests.*

<div><strong>200</strong>: Success, devicesVisibleToGuests returned.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Customer id, location id, or WifiNetwork does not exist.</div>
<div><strong>422</strong>: Device mac validation failed.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.removeDeviceVisibleToGuests`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** | mac to be removed |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/wifiNetwork/accessZones`
*Create a new WiFi Access Zone*

<div><strong>200</strong>: Success, all access zones returned</div>
<div><strong>400</strong>: Required fields missing</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Customer id, location id, or WifiNetwork does not exist</div>
<div><strong>422</strong>: Validation failed</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postWifiAccessZone`

**Required to call:** `id` (path), `locationId` (path), `description` (formData), `type` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `description` | formData | string | **REQUIRED** | name of access zone |
| `type` | formData | string | **REQUIRED** | for now, must be 'guests' |
| `accessibleDevices` | formData | string | optional | macs of home devices visible to this guest access zone |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/wifiNetwork/accessZones/{zoneId}`
*Delete a WiFi Access Zone*

<div><strong>200</strong>: Success, remaining access zones returned</div>
<div><strong>400</strong>: Required fields missing</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Customer id, location id, or WifiNetwork does not exist</div>
<div><strong>405</strong>: Cannot delete a read-only access zone</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteWifiAccessZone`

**Required to call:** `id` (path), `locationId` (path), `zoneId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `zoneId` | path | number | **REQUIRED** | id of access zone |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/wifiNetwork/accessZones/{zoneId}`
*Update an access zone*

<div><strong>200</strong>: Success, wifiNetwork returned</div>
<div><strong>400</strong>: Required fields missing</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Customer id, location id, or WifiNetwork does not exist</div>
<div><strong>422</strong>: Validation failed</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchAccessZone`

**Required to call:** `id` (path), `locationId` (path), `zoneId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `zoneId` | path | number | **REQUIRED** | id of access zone |
| `description` | formData | string | optional |  |
| `accessibleDevices` | formData | string | optional | array of home macs[] visible to this access zone |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/wifiNetwork/accessZones/{zoneId}/keys/{keyId}/invitations`
*Update home devices visible to guests.*

<div><strong>200</strong>: Success, Invitation returned.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Customer id, location id, or WifiNetwork accessZone zoneId/keyId does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getWifiInvitationById`

**Required to call:** `id` (path), `locationId` (path), `zoneId` (path), `keyId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `zoneId` | path | string | **REQUIRED** |  |
| `keyId` | path | number | **REQUIRED** | keys id be added |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/wifiNetwork/accessZones/{zoneId}/accessibleDevices/{mac}`
*Add a device mac to a WiFi Access Zone*

<div><strong>200</strong>: Success, all access zones returned</div>
<div><strong>400</strong>: Required fields missing</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Customer id, location id, or WifiNetwork does not exist</div>
<div><strong>422</strong>: Validation failed</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postDeviceToAccessZone`

**Required to call:** `id` (path), `locationId` (path), `zoneId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `zoneId` | path | number | **REQUIRED** | id of access zone |
| `mac` | path | string | **REQUIRED** | the device mac to be added to the access zone |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/wifiNetwork/accessZones/{zoneId}/accessibleDevices/{mac}`
*Delete a device mac from a WiFi Access Zone*

<div><strong>200</strong>: Success, all access zones returned</div>
<div><strong>400</strong>: Required fields missing</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Customer id, location id, or WifiNetwork does not exist</div>
<div><strong>422</strong>: Validation failed</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteDeviceFromAccessZone`

**Required to call:** `id` (path), `locationId` (path), `zoneId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `zoneId` | path | number | **REQUIRED** | id of access zone |
| `mac` | path | string | **REQUIRED** | the device mac to be added to the access zone |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/bleMode`
*Enable or Disable BLE beaconing for all Pods at a location for Pod location services (e.g. for Pods Naming).*

<div>With the mode of "on", all connected pods at this location will have their bluetooth beacon turned on for locating purposes. Each BLE beacon contains the serial number of the transmitting Pod. A setting of "off", turns off the BLE beaconing for all Pods. With mode set to "wps", all connected pods at this location will have their bluetooth beacon turned on for WPS related proximity measurements.</div>
<div><strong>200</strong>: Success, your new info looks good.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist.</div>
<div><strong>422</strong>: bleMode must be defined.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putBleMode`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mode` | formData | string | optional | on/off/wps/connectable |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/bleMode`
*Enable or Disable BLE beaconing for the specific Pod at a location.*

<div>With the mode of "on", all connected pods at this location will have their bluetooth beacon turned on for locating purposes. Each BLE beacon contains the serial number of the transmitting Pod. A setting of "off", turns off the BLE beaconing for all Pods. With mode set to "wps", all connected pods at this location will have their bluetooth beacon turned on for WPS related proximity measurements.</div>
<div><strong>200</strong>: Success, your new info looks good.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist.</div>
<div><strong>422</strong>: bleMode must be defined.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putBleModeForNode`

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `nodeId` | path | string | **REQUIRED** |  |
| `mode` | formData | string | optional | on/off/wps/connectable |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/ledMode`
*Update the LED mode on a particular Node for a Location ID.*

When the mode is set to "locate", the Node with that ID at this locationId, will have its LED blinked for locating purposes. The mode is set to "normal" to return the LED to its normal mode of operation.
<div><strong>200</strong>: Success, your new info looks good.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist.</div>
<div><strong>422</strong>: ledMode must be defined.</div>
<div><strong>422</strong>: ledMode must be "locate" or "normal".</div>
<div><strong>422</strong>: nodeId must be defined.</div>
<div><strong>425</strong>: nodeId must belong to the location.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putLedMode`

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `nodeId` | path | string | **REQUIRED** |  |
| `mode` | formData | string | optional | locate/normal |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/speedTestResults`
*retrieve the speed test result for a node.*

<div><strong>200</strong>: Success, run.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist.</div>
<div><strong>422</strong>: locationId or nodeId isn't defined.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>503</strong>: Service Unavailable.</div>

operationId: `Customer.prototype.getSpeedTestResults`

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `nodeId` | path | string | **REQUIRED** |  |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number | optional | X # of days/hours/minutes |
| `showFailedSpeedTests` | query | boolean | optional | Show failed speed tests |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/speedTestResults/{requestId}`
*retrieve single speed test result by request id for a node.*

<div><strong>200</strong>: Success.</div>
<div><strong>422</strong>: locationId or nodeId isn't defined.</div>
<div><strong>404</strong>: Speed test not found.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>503</strong>: Service Unavailable.</div>

operationId: `Customer.prototype.getSpeedTestResultsByRequestId`

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path), `requestId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `nodeId` | path | string | **REQUIRED** |  |
| `requestId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/speedTest`
*Run speed test for a node.*

<div><strong>200</strong>: Success, run.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Customer, location or node does not exists.</div>
<div><strong>422</strong>: Invalid test type.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postSpeedTest`

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `nodeId` | path | string | **REQUIRED** |  |
| `serverId` | formData | number | optional |  |
| `uplinkType` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/ispSpeedTest`
*Run ISP speed test for GW node on mobile request.*

<div><strong>200</strong>: Success, run.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Customer or location does not exists.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postRunMobileIspSpeedTest`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `requestId` | formData | string | optional |  |
| `serverId` | formData | number | optional |  |
| `uplinkType` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/ispSpeedTestConfiguration`
*Enable|Disable ispSpeedTestConfiguration to schedule speed tests.*

<div><strong>200</strong>: Success, run.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Customer or location does not exists.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putIspSpeedTestConfiguration`

**Required to call:** `id` (path), `locationId` (path), `enable` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `enable` | formData | string | **REQUIRED** | boolean but marked as 'any' because our mobile app platforms mixed string and boolean primitive |
| `enableAllNodes` | formData | string | optional | boolean but treated as a string since it is optional |
| `downloadLimit` | formData | number | optional | download limit |
| `uploadLimit` | formData | number | optional | upload limit |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/networkMode`
*Get the current Network Mode for a Location ID.*

<div><strong>200</strong>: Success, current NetworkMode returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or NetworkMode does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getNetworkMode`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/networkMode`
*Update the Network Mode for a Location ID.*

<div><strong>200</strong>: Success, your new info looks good.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putNetworkMode`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkMode` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/reboot`
*Reboot all nodes on location*

Hardware reboot all online nodes on a location. Wait delay (seconds) before triggering a reboot.

If delay parameter is not provided, we will default to 1 second. Delay parameter must be between 0 and 100000 (1 day and 3 hours) seconds.

operationId: `Customer.prototype.rebootLocation`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location id |
| `delay` | formData | number | optional | Reboot delay in seconds |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `404` Customer or location not found; `422` Invalid request; `500` Unhandled API error

#### `PUT` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/reboot`
*Reboot node on location*

Hardware reboot node on a location. Wait delay (seconds) before triggering a reboot.

If delay parameter is not provided, we will default to 1 second. Delay parameter must be between 0 and 100000 (1 day and 3 hours) seconds.

operationId: `Customer.prototype.rebootNode`

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location id |
| `nodeId` | path | string | **REQUIRED** | Node id |
| `delay` | formData | number | optional | Reboot delay in seconds |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `404` Customer, location, or node not found; `422` Invalid request; `500` Unhandled API error

#### `POST` `/Customers/{id}/locations/{locationId}/optimize`
*Manually initiate an Optimize request for a Location ID.*

<div><strong>200</strong>: Success, optimize request sent.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.optimize`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `forcePcs` | formData | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/appFacade/dashboard`
*Get the current speed test aggregation result for a Location ID.*

<div><strong>200</strong>: Success, current speedTest result and most active devices returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or NetworkMode does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getSpeedTestResultsForApp`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `excludeDevices` | query | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/capabilities`
*Get the non-base feature capabilities supported by a particular Location ID.*

<div>The controller will implement logic to determine the non-base features supported by the Pods in the location ID. The feature capability is determined on the system level, and not per individual Pod.</div>
<div>The mobile apps or other WebUIs should only show the UI for a feature if the disabled value equals "false".</div>
<div>&nbsp;</div>
<div><strong>200</strong>: Success, current Capabilities returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getLocationCapabilities`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/persons/{personId}/freeze/autoExpire`
*Put all devices from a person to be frozen for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.putPersonFreezeAutoExpire`

**Required to call:** `id` (path), `locationId` (path), `personId` (path), `expiresAt` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |
| `expiresAt` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/persons/{personId}/freeze/autoExpire`
*Delete all devices from a person to be frozen for a Location ID.*

<div><strong>204</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.deletePersonFreezeAutoExpire`

**Required to call:** `id` (path), `locationId` (path), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/persons/{personId}/freeze/suspend`
*Put a person suspend for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.putPersonFreezeSuspend`

**Required to call:** `id` (path), `locationId` (path), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |
| `deleteAllExceptSuspend` | formData | boolean | optional |  |
| `enable` | formData | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/persons/{personId}/freeze/suspend`
*Delete person suspend for a Location ID.*

<div><strong>204</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.deletePersonFreezeSuspend`

**Required to call:** `id` (path), `locationId` (path), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/persons/{personId}/freeze/forever`
*Put a person forever freeze for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.putPersonFreezeForever`

**Required to call:** `id` (path), `locationId` (path), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |
| `deleteAllExceptSuspend` | formData | boolean | optional |  |
| `enable` | formData | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/persons/{personId}/freeze/forever`
*Delete a person forever freeze for a Location ID.*

<div><strong>204</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.deletePersonFreezeForever`

**Required to call:** `id` (path), `locationId` (path), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/persons/{personId}/freeze/{freezeTemplateId}`
*Post a shared schedule uuid freeze for a person for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>404</strong>: FreezeTemplateId not found.</div>
<div><strong>404</strong>: Person not found.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.postPersonFreeze`

**Required to call:** `id` (path), `locationId` (path), `personId` (path), `freezeTemplateId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |
| `freezeTemplateId` | path | string | **REQUIRED** | Valid templates are uuids |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/persons/{personId}/freeze/{freezeTemplateId}`
*Put a person to be frozen for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing shared location freeze schedules.</div>

operationId: `Customer.prototype.putPersonFreeze`

**Required to call:** `id` (path), `locationId` (path), `personId` (path), `freezeTemplateId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |
| `freezeTemplateId` | path | string | **REQUIRED** | Valid templates are 'untilMidinight', 'schoolNights', etc. |
| `deleteAllExceptSuspend` | formData | boolean | optional |  |
| `schedules` | formData | string | optional |  |
| `enable` | formData | boolean | optional |  |
| `name` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/persons/{personId}/freeze/{freezeTemplateId}`
*Delete a person to be frozen for a Location ID.*

<div><strong>204</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.deletePersonFreeze`

**Required to call:** `id` (path), `locationId` (path), `personId` (path), `freezeTemplateId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |
| `freezeTemplateId` | path | string | **REQUIRED** | Valid templates are 'untilMidinight', 'schoolNights', etc. |

**Possible responses:** `204` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/persons/{personId}/freezes`
*Delete a person to be frozen for a Location ID.*

<div><strong>204</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.deletePersonAllFreeze`

**Required to call:** `id` (path), `locationId` (path), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/devices/{mac}/freeze/autoExpire`
*Put a device to be frozen for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.putDeviceFreezeAutoExpire`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `expiresAt` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `expiresAt` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/devices/{mac}/freeze/autoExpire`
*Delete a device to be frozen for a Location ID.*

<div><strong>204</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.deleteDeviceFreezeAutoExpire`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/devices/{mac}/freeze/suspend`
*Put a device suspend for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.putDeviceFreezeSuspend`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `deleteAllExceptSuspend` | formData | boolean | optional |  |
| `enable` | formData | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/devices/{mac}/freeze/suspend`
*Delete a device suspend for a Location ID.*

<div><strong>204</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: MAC address does not exist or is invalid.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.deleteDeviceFreezeSuspend`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/devices/{mac}/freeze/forever`
*Put a device forever freeze for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.putDeviceFreezeForever`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `deleteAllExceptSuspend` | formData | boolean | optional |  |
| `enable` | formData | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/devices/{mac}/freeze/forever`
*Delete a device forever freeze for a Location ID.*

<div><strong>204</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: MAC address does not exist or is invalid.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.deleteDeviceFreezeForever`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/devices/{mac}/freeze/residentialGwManaged`
*Put a device residentialGwManaged freeze for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.putDeviceFreezeResidentialGwManaged`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `deleteAllExceptSuspend` | formData | boolean | optional |  |
| `schedules` | formData | string | optional |  |
| `enable` | formData | boolean | optional |  |
| `name` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/devices/{mac}/freeze/residentialGwManaged`
*Delete a device residentialGwManaged freeze for a Location ID.*

<div><strong>204</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: MAC address does not exist or is invalid.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.deleteDeviceFreezeResidentialGwManaged`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/devices/{mac}/freeze/{freezeTemplateId}`
*Post a shared schedule uuid freeze for a device for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>404</strong>: FreezeTemplateId not found</div>
<div><strong>404</strong>: Device not found</div>
<div><strong>422</strong>: GroupOfUnassignedDevices has active freeze schedule</div>
<div><strong>422</strong>: Person has active freeze schedule</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.postDeviceFreeze`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `freezeTemplateId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `freezeTemplateId` | path | string | **REQUIRED** | Valid templates are uuids |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/devices/{mac}/freeze/{freezeTemplateId}`
*Put a device to be frozen for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing shared location freeze schedules.</div>

operationId: `Customer.prototype.putDeviceFreeze`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `freezeTemplateId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `freezeTemplateId` | path | string | **REQUIRED** | Valid templates are 'untilMidinight', 'schoolNights', etc. |
| `deleteAllExceptSuspend` | formData | boolean | optional |  |
| `schedules` | formData | string | optional |  |
| `enable` | formData | boolean | optional |  |
| `name` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/devices/{mac}/freeze/{freezeTemplateId}`
*Delete a device to be frozen for a Location ID.*

<div><strong>204</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: MAC address does not exist or is invalid.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.deleteDeviceFreeze`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `freezeTemplateId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `freezeTemplateId` | path | string | **REQUIRED** | Valid templates are 'untilMidinight', 'schoolNights', etc. |

**Possible responses:** `204` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/devices/{mac}/freezes`
*Delete/clear all device freezes templateIds for a mac.*

<div><strong>204</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.deleteAllDeviceFreezes`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/freeze/autoExpire`
*Get all devices/persons except some to be frozen for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.getLocationFreezeAutoExpire`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/freeze/autoExpire`
*Delete the location freeze/autoExpire for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.deleteLocationFreezeAutoExpire`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/freeze/autoExpire`
*Put all devices except some to be frozen for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.patchLocationFreezeAutoExpire`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `includedDeviceMacs` | formData | string | optional |  |
| `includedPersonIds` | formData | string | optional |  |
| `expiresAt` | formData | string | optional |  |

**Possible responses:** `204` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/wifiNetwork/ssid`
*Get the current WiFi SSID for a Location ID.*

<div><strong>200</strong>: Success, current Wifi Network returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or WifiNetwork does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getSsid`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/secondaryNetworks/fronthauls`
*Get the Front Haul Portal configs for a given Location ID.*

<div><strong>200</strong>: Success, FrontHaul Networks returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or secondary network does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getFrontHaulNetworks`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/secondaryNetworks/fronthauls`
*Create a Front Haul Network for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or NetworkId does not exist and is not known to Plume</div>
<div><strong>422</strong>: NetworkId/SSIDs must be the unique and valid values.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postFrontHaul`

**Required to call:** `id` (path), `locationId` (path), `ssid` (formData), `encryptionKey` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | formData | string | optional |  |
| `ssid` | formData | string | **REQUIRED** |  |
| `enable` | formData | boolean | optional |  |
| `encryptionKey` | formData | string | **REQUIRED** |  |
| `accessZone` | formData | string | optional |  |
| `wpaMode` | formData | string | optional |  |
| `wpaModes` | formData | string | optional | Object with { freqBand24: wpaMode, freqBand5: wpaMode, freqBand6: sae } interface. For possible wpaMode values look at the wpaMode property. |
| `ssidBroadcast` | formData | boolean | optional |  |
| `nodeEnablement` | formData | string | optional |  |
| `radioEnablement` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals`
*Get the Captive Portal configs for a given Location ID.*

<div><strong>200</strong>: Success, CaptivePortal Networks returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or secondary networks does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getCaptivePortalNetworks`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals`
*Create a Captive Portal Network for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or NetworkId does not exist and is not known to Plume</div>
<div><strong>422</strong>: NetworkId/SSIDs must be the unique and valid values.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postCaptivePortal`

**Required to call:** `id` (path), `locationId` (path), `ssid` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | formData | string | optional |  |
| `ssid` | formData | string | **REQUIRED** |  |
| `enable` | formData | boolean | optional |  |
| `encryptionKey` | formData | string | optional |  |
| `bandwidthLimit` | formData | string | optional | attributes: "enabled" boolean, "type": "absolute"\|"percentage", "upload"/"download" - either as percentage or absolute (Mbps) |
| `sessionTimeLimitSec` | formData | number | optional |  |
| `wpaMode` | formData | string | optional |  |
| `language` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/secondaryNetworks/fronthauls/{networkId}`
*Delete a Front Haul for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id/NetworkId does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteFrontHaul`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/secondaryNetworks/fronthauls/{networkId}`
*Update a Front Haul for a given Location ID/NetworkId.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or NetworkId does not exist and is not known to Plume</div>
<div><strong>422</strong>: NetworkId/SSIDs must be the unique and valid values.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchFrontHaul`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `ssid` | formData | string | optional |  |
| `enable` | formData | boolean | optional |  |
| `encryptionKey` | formData | string | optional |  |
| `accessZone` | formData | string | optional |  |
| `wpaMode` | formData | string | optional |  |
| `wpaModes` | formData | string | optional | Object with { freqBand24: wpaMode, freqBand5: wpaMode, freqBand6: sae } interface. For possible wpaMode values look at the wpaMode property. |
| `ssidBroadcast` | formData | boolean | optional |  |
| `nodeEnablement` | formData | string | optional |  |
| `radioEnablement` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/{networkId}`
*Delete a CaptivePortal for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id/NetworkId does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteCaptivePortal`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/{networkId}`
*Update a Captive Portal for a given Location ID/NetworkId.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or NetworkId does not exist and is not known to Plume</div>
<div><strong>422</strong>: NetworkId/SSIDs must be the unique and valid values.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchCaptivePortal`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `ssid` | formData | string | optional |  |
| `enable` | formData | boolean | optional |  |
| `encryptionKey` | formData | string | optional |  |
| `bandwidthLimit` | formData | string | optional | attributes: "enabled" boolean, "type": "absolute"\|"percentage", "upload"/"download" - either as percentage or absolute (Mbps) |
| `wpaMode` | formData | string | optional |  |
| `sessionTimeLimitSec` | formData | number | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/{networkId}/guests`
*Fetch the list of Guests which were logged into the given captivePortal network during the current day.*

<div><strong>200</strong>: Success, CaptivePortal Networks returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or secondary networks does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getCaptivePortalGuests`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `orderBy` | query | string | optional | Order by: <connectionTime> |
| `limit` | query | number | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/secondaryNetworks/fronthauls/{networkId}/dpp`
*Get the current DPP configurator for a Location ID.*

<div><strong>200</strong>: Success, current DPP configurator returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getFrontHaulsDpp`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/secondaryNetworks/fronthauls/{networkId}/dpp`
*Create the DPP setting for a Fronthaul Network.*

<div><strong>202</strong>: Success, new DPP configurator generated.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or Fronthaul Network does not exist.</div>
<div><strong>422</strong>: Invalid keys.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postFrontHaulsDpp`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `enabled` | formData | boolean | optional | should we configure dpp for this network - defaults to true |
| `curve` | formData | string | optional | one of predefined elliptic curves, - optional,  if missing in request default to prime256v1 |
| `privateKey` | formData | string | optional | privateKey, must also provide public part if present, optional |
| `publicKey` | formData | string | optional | publicKey |

**Possible responses:** `202` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/secondaryNetworks/fronthauls/{networkId}/dpp/bootstrapUris`
*Create a bootstrap for DPP setting for a Fronthaul Network.*

<div><strong>200</strong>: Success, new DPP configurator generated.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or Fronthaul Network does not exist.</div>
<div><strong>422</strong>: Invalid curve.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postFrontHaulsDppBootstrap`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `curve` | formData | string | optional | one of predefined elliptic curves, - optional,  if missing in requset default to prime256v1 |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/dpp/enrollments`
*Create and persist a list of DPP enrollments*

<div><strong>202</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or wifi network does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putDppEnrollments`

**Required to call:** `id` (path), `locationId` (path), `enrollments` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `enrollments` | body | array | **REQUIRED** |  |

**Possible responses:** `202` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/secondaryNetworks/fronthauls/{networkId}/dpp/enrollments`
*Create an enrollment for DPP setting for a fronthaul secondary network.*

<div><strong>202</strong>: Success, new DPP configurator generated.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or wifi network does not exist.</div>
<div><strong>404</strong>: Configurator keys for network not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postFrontHaulsDppEnrollment`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `bootstrapUri` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `bootstrapUri` | formData | string | **REQUIRED** |  |

**Possible responses:** `202` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/securityPolicy/ohp/locationIdentifier`
*Get the current OHP identifier for a Location ID.*

<div><strong>200</strong>: Success, current DPP configurator returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getOhpLocationIdentifier`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/onboardingLocationIdentifier`
*Get the onboarding identifier for a Location ID.*

<div><strong>200</strong>: Success, current DPP configurator returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getOnboardingLocationIdentifier`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/{networkId}/networkUsage`
*Fetch the Captive Portal Network Usage stats for the given network.*

<div><strong>200</strong>: Success, CaptivePortal Networks returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or secondary networks does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postCaptivePortalNetworkUsageStats`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `inclusions` | formData | string | optional | Fields to include in response |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/{networkId}/guestEmailCollectionInfo`
*Fetch the Captive Portal Network guest info download availability for the given network.*

<div><strong>200</strong>: Success, CaptivePortal Networks guest info download availability returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or secondary networks does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getCaptivePortalGuestEmailCollectionInfo`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `duration` | query | number | optional | number of days for how far back in history for data |
| `limit` | query | number | optional | limit how many emails we wish to return |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/{networkId}/enableGuestEmailCollection`
*Patch the Captive Portal Network to be compliant for guest email collection.*

<div><strong>200</strong>: Success, CaptivePortal Networks has been patched.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or secondary networks does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postCaptivePortalEnableGuestEmailCollection`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/{networkId}/downloadGuestDetailsDirect`
*Download Captive Portal Guest details for a given Location ID/NetworkId without accessing Amazon S3.*

<div><strong>204</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or CaptivePortal Network does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getCaptivePortalDetailsDirect`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `duration` | query | number | optional |  |
| `limit` | query | number | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/{networkId}/authorizedClients`
*Get CaptivePortal authorized clients*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id/NetworkId does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getCaptivePortalAuthorizedClients`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/{networkId}/authorizedClients`
*Post CaptivePortal authorized clients*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id/NetworkId does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postCaptivePortalAuthorizedClients`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `mac` (formData), `expireAt` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `mac` | formData | string | **REQUIRED** |  |
| `expireAt` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/{networkId}/authorizedClients/{mac}`
*Delete Authorized Client*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id/NetworkId does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteCaptivePortalAuthorizedClients`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `mac` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/{networkId}/authorizedClients/{mac}`
*Post CaptivePortal authorized clients*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id/NetworkId does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchCaptivePortalAuthorizedClients`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `mac` (path), `expireAt` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `mac` | path | string | **REQUIRED** |  |
| `expireAt` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/devices/{mac}/clientSteering`
*Toggle auto:on/off client steering for a device.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: Invalid mac address.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchDeviceClientSteering`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** | device mac address |
| `auto` | formData | boolean | optional |  |
| `steeringClass` | formData | string | optional | override deviceTypeId for testing purposes |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/councilman/resync`
*Push Security Configurations to Councilman.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putCouncilmanResync`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `204` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/securityConfiguration`
*Patch Security Configurations for location (preferredIntelligence, etc)*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: Invalid securityConfig.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchSecurityConfiguration`

**Required to call:** `id` (path), `locationId` (path), `securityConfig` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `securityConfig` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/bandSteering`
*Enable/disable band steering for a Location ID (deprecated)*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putBandSteering`

**Required to call:** `id` (path), `locationId` (path), `auto` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `auto` | formData | boolean | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/bandSteering`
*Set mode for band steering*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: Invalid mode.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchLocationBandSteering`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mode` | formData | string | optional | auto \|\| enable \|\| disable |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/controlMode`
*Get control mode for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getControlMode`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/controlMode`
*Set control mode for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putControlMode`

**Required to call:** `id` (path), `locationId` (path), `mode` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mode` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/monitorMode`
*Enable/disable monitor mode for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putMonitorMode`

**Required to call:** `id` (path), `locationId` (path), `enable` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `enable` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/optimizations`
*Enable/disable optimizations for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: Invalid dfsMode, prefer160MhzMode, hopPenalty or preCACScheduler provided.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putOptimizations`

**Required to call:** `id` (path), `locationId` (path), `auto` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `auto` | formData | string | **REQUIRED** | defaults to true |
| `dfsMode` | formData | string | optional | enum of values include: auto, enable, disable, demo, HomeNonDFSChannels, usDfs, deviceAware |
| `prefer160MhzMode` | formData | string | optional | enum of values include: auto, enable, disable |
| `hopPenalty` | formData | string | optional | enum of values include: auto, low, medium, high |
| `preCACScheduler` | formData | string | optional | enum of values include: auto, enable, disable |
| `maxBandwidth` | formData | string | optional | Defines maximum bandwidth used per frequency band. |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/optimizations`
*Enable/disable optimizations for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: Invalid dfsMode, prefer160MhzMode, zeroWaitDfsMode, hopPenalty or preCACScheduler provided.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchOptimizations`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `auto` | formData | string | optional | defaults to true |
| `dfsMode` | formData | string | optional | enum of values include: auto, enable, disable, demo, HomeNonDFSChannels, usDfs, deviceAware |
| `prefer160MhzMode` | formData | string | optional | enum of values include: auto, enable, disable |
| `zeroWaitDfsMode` | formData | string | optional | enum of values include: auto, enable, disable |
| `hopPenalty` | formData | string | optional | enum of values include: auto, low, medium, high |
| `preCACScheduler` | formData | string | optional | enum of values include: auto, enable, disable |
| `maxBandwidth` | formData | string | optional | Defines maximum bandwidth used per frequency band. |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/locale`
*Configure locale values for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: Region value is not valid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putLocale`

**Required to call:** `id` (path), `locationId` (path), `region` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `region` | formData | string | **REQUIRED** | during optimizations, used to determine allowed WiFi channels. Possible values: US, SINGAPORE, UK, EU, CANADA, JP. |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/authorizations`
*Get the number of authorized leaf pods for a Location ID.*

<div>Number of leaf pods that are authorized to be claimed and be a part of the Plume network</div>
<div><strong>200</strong>: Success, numPodsAuthorized returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getAuthorizations`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/authorizations`
*Configure number of authorized leaf pods for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>400</strong>: Required fields are missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putAuthorizations__put_Customers_{id}_locations_{locationId}_authorizations`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `numPodsAuthorized` | formData | number | optional | number of leaf pods that are authorized to be claimed and be a part of the Plume network |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/nodeAuthorizations`
*Configure number of authorized leaf pods grouped by model id for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>400</strong>: Required fields are missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putAuthorizations__put_Customers_{id}_locations_{locationId}_nodeAuthorizations`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `numNodesAuthorized` | formData | string | optional | number of leaf pods grouped by model id that are authorized to be claimed and be a part of the Plume network |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/wanSettings`
*DEPRECATED: Get the WAN Settings for a Location ID.*

<div><strong>200</strong>: Success, WAN Settings returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getLocationWanSettings`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/wanSettings`
*DEPRECATED: Persist WAN Settings for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: Required fields are not valid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putLocationWanSettings`

**Required to call:** `id` (path), `locationId` (path), `wanSettings` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `wanSettings` | body | LocationWanSettings | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/wanConfiguration`
*Get WAN Configuration for a Location ID.*

<div><strong>200</strong>: Success, WAN Settings returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getLocationWanConfiguration`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/wanConfiguration`
*Persist WAN Configuration for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: Required fields are not valid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putLocationWanConfiguration`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `pppoe` | formData | string | optional |  |
| `uplink` | formData | string | optional |  |
| `staticIPv4` | formData | string | optional |  |
| `publishedWithBLE` | formData | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/persistentConfigs`
*Delete persistent data/configs from node in runtime.*

<div><strong>204</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location or Node, does not exist.</div>
<div><strong>422</strong>: Required fields are not valid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteNodePersistentConfigs`

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `nodeId` | path | string | **REQUIRED** | node id |
| `deleteAllPersistentConfigs` | formData | boolean | optional | whether all persistent config data or just GW-offline data will be deleted |

**Possible responses:** `204` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/networkConfiguration/dhcp`
*Get current DHCP Configuration details for a Location ID.*

<div><strong>200</strong>: Success, current dhcp returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or dhcp does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDhcp`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/networkConfiguration/dhcp`
*Record or update a new DHCP subnet/subnetMask for a Location ID.*

<div><strong>200</strong>: Success, DHCP are returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>422</strong>: subnet value is empty, or invalid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putDhcp`

**Required to call:** `id` (path), `locationId` (path), `subnet` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `subnet` | formData | string | **REQUIRED** |  |
| `subnetMask` | formData | string | optional |  |
| `startIp` | formData | string | optional |  |
| `endIp` | formData | string | optional |  |
| `enableServer` | formData | boolean | optional | should the DHCP server be enabled |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/networkConfiguration/dhcp`
*Update DHCP configuration parameters.*

<div><strong>200</strong>: Success, DHCP config is returned.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>422</strong>: DHCP not configured, use PUT to configure DHCP.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchDhcp`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `enableServer` | formData | boolean | optional | should the DHCP server be enabled |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/networkConfiguration/dhcpReservations/{mac}`
*Get current DHCP IP reservation details for a Location ID.*

<div><strong>200</strong>: Success, current DhcpReservation returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or DhcpReservation does not exist.</div>
<div><strong>422</strong>: mac is empty, or invalid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDhcpReservation`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/networkConfiguration/dhcpReservations/{mac}`
*Record or update a new DHCP IP Reservation for a particular MAC address at a Location ID.*

<div><strong>200</strong>: Success, all DHCP Reservations are returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>412</strong>: Subnet prefix is unknown.</div>
<div><strong>422</strong>: IP/mac value is empty, or invalid, or tag length is invalid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putDhcpReservation`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `ip` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `ip` | formData | string | **REQUIRED** |  |
| `hostName` | formData | string | optional |  |
| `tag` | formData | string | optional | Optional override for the dnsmasq tag stored on the reservation. When omitted, the cloud derives the tag from the reservation IP: a public/RIPv2 range yields its range tag, the LAN range yields none. Supplying a value overrides this derivation. |
| `disableIpInUseCheck` | formData | boolean | optional | When true, skips the check that rejects reserving an IP still held by another non-stale device (client offline 24h or less). Defaults to false so the check stays on. |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/networkConfiguration/dhcpReservations/{mac}`
*Delete a current DHCP IP reservation and the associated port forwarding entries for a particular MAC address at a Location ID.*

<div><strong>200</strong>: Success, remaining DhcpReservations are returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: NetworkConfiguration or DhcpReservation is empty.</div>
<div><strong>422</strong>: mac is empty or invalid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteDhcpReservation`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/networkConfiguration/dhcpReservations`
*Get current DHCP IP reservation details for a Location ID.*

<div><strong>200</strong>: Success, current DhcpReservation returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or DhcpReservation does not exist.</div>
<div><strong>422</strong>: mac is empty, or invalid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDhcpReservations`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/networkConfiguration/multicast`
*Update the multicast settings for a Location ID.*

Supported modes for individual settings are:
* igmpSnooping: enable/disable/auto
* igmpProxy: igmpv1/igmpv2/igmpv3/disable/auto
* mldProxy: mldv1/mldv2/disable/disable/auto
* multicastToUnicast: enable/disable/auto

<div><strong>200</strong>: Success, new multicast settings saved.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>422</strong>: Input validation error, see output for details.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchMulticast`

**Required to call:** `id` (path), `locationId` (path), `multicast` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `multicast` | body | Multicast | **REQUIRED** | multicast object |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/networkConfiguration/ethernetLan`
*Update the ethernetLan setting for a Location ID.*

Supported modes are:
* enable/disable/auto

<div><strong>200</strong>: Success, new ethernetLan settings saved.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>422</strong>: Input validation error, see output for details.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchEthernetLan`

**Required to call:** `id` (path), `locationId` (path), `ethernetLan` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `ethernetLan` | body | EthernetLan | **REQUIRED** | ethernetLan object |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/networkConfiguration/mapT`
*Update the Map-T settings for a Location ID via networkConfiguration.*

<div><strong>202</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location ID does not exist.</div>
<div><strong>422</strong>: Input validation error, see output for details.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchMapT`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mode` | formData | string | optional | Any of "auto", "enable", "disable" |
| `monitoring` | formData | string | optional | Any of "auto", "enable", "disable" |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/networkConfiguration/persistConfigurationOnGateway`
*Update settings for persistConfigurationOnGateway.*

Supported modes are:
* enable/disable/auto

<div><strong>200</strong>: Success, new ethernetLan settings saved.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>422</strong>: Input validation error, see output for details.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putPersistConfigurationOnGateway`

**Required to call:** `id` (path), `locationId` (path), `persistConfigurationOnGateway` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `persistConfigurationOnGateway` | body | EthernetLan | **REQUIRED** | ethernetLan object |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/networkConfiguration/upnp`
*Get the current UPnP setting for a Location ID.*

<div><strong>200</strong>: Success, current Upnp returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getUpnp`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/networkConfiguration/upnp`
*Update the UPnP setting for a Location ID.*

<div><strong>200</strong>: Success, new Upnp saved.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>422</strong>: Upnp value is empty.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putUpnp`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `enabled` | formData | string | optional | DEPRECATED: boolean but marked as 'any' because our mobile app platforms mixed string and boolean primitive |
| `mode` | formData | string | optional | Possible values enable/disable/auto |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/networkConfiguration/dnsServers`
*Get the current DNS IP addresses and settings for a Location ID.*

<div><strong>200</strong>: Success, current DNS server settings returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: NetworkConfiguration or DNS server settings does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDnsServers`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/networkConfiguration/dnsServers`
*Update the DNS IPv4 server addresses for a Location ID.*

<div><strong>200</strong>: Success, new DNS Servers saved.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>422</strong>: primaryDns or secondaryDns DNS Servers value is empty.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putDnsServers`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `primaryDns` | formData | string | optional |  |
| `secondaryDns` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/networkConfiguration/home`
*Get the current overall settings and status of the Advanced Networking settings for a Location ID.*

<div><strong>200</strong>: Success, current networkConfiguration settings returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getNetworkConfigurationHome`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/networkConfiguration/dhcpReservations/{mac}/portForward`
*Record a new Port Forwarding entry for an existing DHCP IP reservation tied to a MAC address at a Location ID.*

<div><strong>200</strong>: Success, all PortForwards are returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>422</strong>: networkConfiguration, dhcpReservation, PortForward is empty.</div>
<div><strong>422</strong>: mac is empty, or invalid, externalPort/internalPort is out of range, or protocol is invalid, or duplicate externalPort.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postPortForward`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `externalPort` | formData | string | optional |  |
| `internalPort` | formData | string | optional |  |
| `protocol` | formData | string | optional |  |
| `name` | formData | string | optional |  |
| `natLoopback` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/networkConfiguration/dhcpReservations/{mac}/portForward/{externalPort}`
*Update an existing Port Forwarding entry for an existing DHCP IP reservation tied to a MAC address at a Location ID.*

<div><strong>200</strong>: Success, all PortForwards are returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>422</strong>: networkConfiguration, dhcpReservation, PortForward is empty.</div>
<div><strong>422</strong>: mac is empty, or invalid, externalPort/internalPort is out of range, or protocol is invalid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putPortForward`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `externalPort` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `externalPort` | path | string | **REQUIRED** |  |
| `internalPort` | formData | string | optional |  |
| `protocol` | formData | string | optional |  |
| `name` | formData | string | optional |  |
| `natLoopback` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/networkConfiguration/dhcpReservations/{mac}/portForward/{externalPort}`
*Delete an existing Port Forwarding entry for an existing DHCP IP reservation tied to a MAC address at a Location ID.*

<div><strong>200</strong>: Success, returns list of remaining port forwards.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: NetworkConfiguration, DhcpReservation or PortForward does not exist.</div>
<div><strong>422</strong>: mac does not exist, or is invalid, or externalPort is empty.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deletePortForward`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `externalPort` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `externalPort` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/networkConfiguration/dhcpReservations/{mac}/portForwards`
*Get all existing Port Forwarding entries for an existing DHCP IP reservation tied to a MAC address at a Location ID.*

<div><strong>200</strong>: Success, current Port Forwarding entries  returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: NetworkConfiguration or dhcpReservations value is empty.</div>
<div><strong>422</strong>: mac is empty or invalid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getPortForwards`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/onboardingCheckpoint`
*Record the new Onboarding Checkpoint for the Location ID.*

<div><strong>200</strong>: Success, most recent checkpoint saved.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist and is not known to Plume</div>
<div><strong>422</strong>: checkpoint value must be defined.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postOnboardingCheckpoint`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `checkpoint` | formData | string | optional | is the last passed onboarding step by the customer: 'PodsAdded' or 'OnboardingComplete'; |
| `podsSeenByBle` | formData | string | optional | is the number of Nodes the app discovered by BLE when the onboarding was completed by the customer, submit with PodsAdded |
| `appOs` | formData | string | optional | is the version of the app used during the onboarding, submit with PodsAdded |
| `osVersion` | formData | string | optional | is the phone OS version used during the onboarding, submit with PodsAdded |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/iosDeviceToken/{deviceToken}`
*Inserts the iOS device token for the Customer ID, which may be used for notification services.*

<div><strong>204</strong>: Success, most recent IOS device Token saved.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>422</strong>: deviceToken value must be defined.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putIosDeviceToken`

**Required to call:** `id` (path), `deviceToken` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `deviceToken` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `GET` `/Customers/{id}/iosDeviceTokens/{deviceToken}/exists`
*Provides feedback as to whether an iOS deviceToken was previously registered for push notifications.*

<div><strong>200</strong>: Success, exists:true|false returned.</div>
<div><strong>404</strong>: customer id does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.iosDeviceTokenExists`

**Required to call:** `id` (path), `deviceToken` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `deviceToken` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/summary`
*DEPRECATED: The system summary for a location including topology, optimizations, and firmware upgrades.*

<div><strong>200</strong>: Success, system info plus topology array returned.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getSummary`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/topology`
*DEPRECATED: The topology for a location including channels and devices.*

Please use the GET /Customers/{id}/locations/{locationId}/forceGraph API as a replacement.
<div><strong>200</strong>: Success, array of Nodes returned.</div>
<div><strong>404</strong>: customer id, location id, or topology does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getTopology`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/forceGraph`
*HTML or JSON (vertices[] + edges[]) used to display a Network Topology.*

<div>The HTML and JSON to initialize and dynamically display and update a Topology.</div>
<div>The JSON can also be used to get a network's list of nodes + devices (a.k.a. vertices) and links (a.k.a., edges).</div><div>&nbsp;</div>
<div><strong>200</strong>: Success, HTML or JSON returned depending on "Accept" HTTP header.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getForceGraph`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `ip` | query | string | optional | deprecated and optional IP address of client displaying the topology |
| `mac` | query | string | optional | optional mac address of client displaying the topology |
| `authKey` | query | string | optional | PubNub authKey |
| `subscribeKey` | query | string | optional | PubNub subscribeKey |
| `view` | query | string | optional | view template override (e.g., iguana) |
| `allSSIDs` | query | boolean | optional |  |
| `showPartnerComponent` | query | boolean | optional |  |
| `showOnlyIot` | query | boolean | optional |  |
| `showAlsoIot` | query | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/thread/graph`
*Get thread graph for the location.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>422</strong>: Multiple validation errors.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getThreadGraph`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/alerts`
*Retrieve active alerts for this location.*

<div><strong>200</strong>: Success, an array of Nodes and an array of Devices returned.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getAlerts`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/alerts/{type}`
*Snooze an alert on a node.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist or nodeId not claimed to this account.</div>
<div><strong>422</strong>: Invalid alert type and/or state.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putSnoozeOnNodeAlert`

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path), `type` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `nodeId` | path | string | **REQUIRED** | id of node |
| `type` | path | string | **REQUIRED** | enum of values include: poorHealth |
| `state` | formData | string | optional | enum of values include: snooze, ignore, performanceAcceptable, reset |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/devices/{mac}/alerts/{type}`
*Snooze an alert on a device.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist or device mac not in this account's recent history.</div>
<div><strong>422</strong>: Invalid alert type and/or state.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putSnoozeOnDeviceAlert`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `type` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** | mac of device |
| `type` | path | string | **REQUIRED** | enum of values include: poorHealth |
| `state` | formData | string | optional | enum of values include: snooze, ignore, performanceAcceptable |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/nodes/{nodeId}`
*Returns a single Node for a Customer ID.*

<div><strong>200</strong>: Success, node returned with locationId field.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: customer id or location id does not exist. Or, nodeId not claimed to this account.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getCustomerNodeById`

**Required to call:** `id` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `nodeId` | path | string | **REQUIRED** | id of node |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/nodes/{nodeId}`
*Delete a node model based on its id.*

<div><strong>204</strong>: The node was successfully deleted.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Node or customer not found.</div>
<div><strong>422</strong>: Node deletion could not be completed.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteNodeLocked`

**Required to call:** `id` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `nodeId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}`
*Returns a single Node for a Location ID with its list of connected devices.*

<div><strong>200</strong>: Success, node returned.</div>
<div><strong>404</strong>: customer id or location id does not exist. Or, nodeId not claimed to this account.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getNodeBySerialNumber`

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `nodeId` | path | string | **REQUIRED** | id of node |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}`
*Rename a particular Node for a Location ID with the option to disable the blinking LED.*

Rename a particular Node for a Location ID with the option to disable the blinking LED with the option "emitMessage":"on" or "off".
<div><strong>200</strong>: Success, a job well done.</div>
<div><strong>400</strong>: Bad request, nickname is undefined or empty string.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location ID or node ID not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.renameNode`

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path), `nickname` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `nodeId` | path | string | **REQUIRED** |  |
| `nickname` | formData | string | **REQUIRED** |  |
| `emitMessage` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}`
*Unclaim a particular Node from a Location ID with the option of preserving the original Package ID.*

<div><strong>204</strong>: Success, a job well done.</div>
<div><strong>400</strong>: Pod already unclaimed.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>403</strong>: the node is online, and can not be unclaimed.<br/> 
<div><strong>404</strong>: location id not found, nodeId missing from URL,<br/> or location has zero owned pods.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.unclaimNode`

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `nodeId` | path | string | **REQUIRED** |  |
| `preservePackId` | formData | boolean | optional | packId should remain the same |
| `removeAccountId` | formData | boolean | optional | delete account id on the inventory node |

**Possible responses:** `204` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/nodes`
*Retrieve the Node settings and status for a Location ID.*

<div><strong>200</strong>: Success, array of Nodes returned.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getNodes`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/nodes`
*Claim a node and all nodes still associated to its Package ID for a Location ID.*

<div><strong>200</strong>: King node claimed and all related claimed nodes are returned.</div>
<div><strong>204</strong>: Valid serial number but zero new claimed nodes.</div>
<div><strong>404</strong>: Unable to find Node with serial number, customer id, or location id.</div>
<div><strong>409</strong>: Node is owned by another customer.</div>
<div><strong>422</strong>: Claiming request exceeded numPodsAuthorized (=leaf pods), accountId+partnerId not unique, and/or monitorMode=true.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.claimNode`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `serialNumber` | formData | string | optional | unique serial number or ID of Node |
| `radioMac24` | formData | string | optional | optional but required for auto-importing, must be a valid mac address |
| `radioMac50` | formData | string | optional | optional but required for auto-importing, must be a valid mac address |
| `radioMac60` | formData | string | optional | optional but required for auto-importing, must be a valid mac address |
| `ethernetMac` | formData | string | optional | optional but required for auto-importing, must be a valid mac address |
| `ethernet1Mac` | formData | string | optional | optional but required for auto-importing, must be a valid mac address |
| `claimKey` | formData | string | optional | optional but required for auto-importing, must be a valid claimKey |
| `model` | formData | string | optional | optional when auto-importing, ignored otherwise |
| `hybridCheck` | formData | boolean | optional | optional when auto-importing, ignored otherwise |
| `nickname` | formData | string | optional | optional node nickname |
| `skipSubscription` | query | boolean | optional | skip subscription update |
| `backhaulDhcpPoolIdx` | formData | number | optional | optional node backhaulDhcpPoolIdx |
| `room` | formData | string | optional | optional room identifier |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/nodes`
*Unclaim all Nodes from a Location ID with the option of preserving the original Package ID.*

<div><strong>204</strong>: Success, a job well done.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id not found in customer service or not found in inventory service.<p/> 
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.unclaimAllNodes`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `preservePackId` | formData | boolean | optional | packId should remain the same |
| `removeAccountId` | formData | boolean | optional | delete account ids on the inventory nodes |
| `doNotFactoryReset` | formData | boolean | optional | notify controller not to initiate a facotry reset |

**Possible responses:** `204` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/devices`
*Get all the devices for a Location ID, including the device name, icon to use, MAC and IP  address, connecting nodes and more.*

All devices with 2g, 5g and 6g channel settings
<div><strong>200</strong>: Success, array of Devices returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDevices`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `daysOffline` | query | number | optional |  |
| `allSSIDs` | query | boolean | optional |  |
| `showPartnerComponent` | query | boolean | optional |  |
| `showOnlyIot` | query | boolean | optional |  |
| `showAlsoIot` | query | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}`
*Returns a single Device for a Location ID.*

<div><strong>200</strong>: Success, device returned.</div>
<div><strong>404</strong>: customer id or location id does not exist. Or, device not found in this network 's history.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDeviceByMac`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** | mac of device |
| `include` | query | string | optional | can be 'bandwidthData', 'chartsData' or both. None means 'bandwidthData' only. |
| `daysOffline` | query | number | optional | exclude devices disconnected longer than daysOffline. |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/devices/{mac}`
*Removes a device for a customer's location id, wiping config and setting a hidden flag.*

<div><strong>204</strong>: Success, device removed from location. </div>
<div><strong>404</strong>: location id or  device not found. </div>
<div><strong>500</strong>: internal server error </div>

operationId: `Customer.prototype.removeDeviceByMac`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** | mac of device |
| `daysOffline` | formData | number | optional | exclude devices disconnected longer than daysOffline. if not set, it will be 31. for older devices, it will return 404, "not found" |

**Possible responses:** `204` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/devices/{mac}`
*Update device*

Update device favorite or nickname properties. You can only change one of these properties at a time.

operationId: `Customer.prototype.patchDevice`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location id |
| `mac` | path | string | **REQUIRED** | Device MAC |
| `favorite` | formData | boolean | optional | Set device as favorite |
| `nickname` | formData | string | optional | Nickname for the device |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `403` Forbidden; `404` Customer, location, or device not found; `422` Invalid request; `500` Unhandled API error

#### `POST` `/Customers/{id}/createOauthAccessToken`
*Create access token with ouath scope.*

<div><strong>200</strong>: Success, access token created and returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.createOauthAccessToken`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `scope` | formData | string | optional |  |
| `ttlSeconds` | formData | number | optional |  |
| `singleToken` | formData | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/userInfo`
*Get customer details with userInfo access token.*

<div><strong>200</strong>: Success, customer details returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.userInfo`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/exists`
*Check if the customer email exists and is known to Plume and returns emailVerified value.*

<div><strong>200</strong>: customer email exists and is known to Plume, emailVerified returned</div>
<div><strong>400</strong>: email is required</div>
<div><strong>404</strong>: customer email does not exist and is not known to Plume</div>
<div><strong>422</strong>: email is not valid</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.emailExists`

**Required to call:** none

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `email` | query | string | optional | Pass the email as an URL parameter. |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/findByEmail/{email}`
*Find customer by email*

This endpoint searches for customer by email, and hashed email (if customerAnonymization feature flag is enabled).
This endpoint is meant to be used by provisioning service.
This endpoint should be accessible only with integration token.

operationId: `Customer.findCustomerByEmail`

**Required to call:** `email` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `email` | path | string | **REQUIRED** | Email address that verification email will be sent to. |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Model not found; `undefined`

#### `POST` `/Customers/resendEmailVerification`
*Resend the verification email.*

<div><strong>204</strong>: Successfully sent email verification.</div>
<div><strong>400</strong>: Customer email is required (for this request).</div>
<div><strong>404</strong>: Unable to find Customer by email address.</div>
<div><strong>409</strong>: Customer email already verified.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.resendEmailVerification`

**Required to call:** none

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `email` | formData | string | optional | Email address that verification email will be sent to. |
| `notificationOptions` | formData | string | optional |  |

**Possible responses:** `204` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/factoryReset`
*Reset specified location settings to default, while keeping claimed nodes intact. Some of the flags can cause a node to be reeboted.*

<div><strong>204</strong>: Success, a job well done.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id not found or nodeId missing from URL
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.factoryReset`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `persons` | formData | boolean | optional | Whether or not to delete person information |
| `onboardingCheckpoints` | formData | boolean | optional | Whether or not to reset onboarding checkpoints |
| `devices` | formData | boolean | optional | Whether or not to delete devices related information |
| `networkConfiguration` | formData | boolean | optional | Whether or not to reset network configuration (triggers node reboot) |
| `wifiNetwork` | formData | boolean | optional | Whether or not to reset wifi network (triggers node reboot) |
| `secondaryNetworks` | formData | boolean | optional | Whether or not to reset secondary network (triggers node reboot) |
| `deviceFreeze` | formData | boolean | optional | Whether or not to reset device freeze templates |
| `deviceNicknames` | formData | boolean | optional | Whether or not to reset device nicknames |
| `nodeNicknames` | formData | boolean | optional | Whether or not to reset node nicknames |
| `managers` | formData | boolean | optional | Whether or not to reset managers of the location |
| `wanConfiguration` | formData | boolean | optional | Whether or not to reset wanConfiguration |

**Possible responses:** `204` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/configs`
*Delete specified location settings, while keeping claimed nodes intact*

<div><strong>204</strong>: Success, a job well done.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id not found or nodeId missing from URL
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteConfigs`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `persons` | formData | boolean | optional | Whether or not to delete person information |
| `onboardingCheckpoints` | formData | boolean | optional | Whether or not to delete onboarding checkpoints |
| `devices` | formData | boolean | optional | Whether or not to delete devices related information |
| `networkConfiguration` | formData | boolean | optional | Whether or not to delete network configuration |
| `wifiNetwork` | formData | boolean | optional | Whether or not to delete wifi network |
| `deviceFreeze` | formData | boolean | optional | Whether or not to delete device freeze templates |
| `deviceNicknames` | formData | boolean | optional | Whether or not to delete device nicknames |
| `nodeNicknames` | formData | boolean | optional | Whether or not to delete node nicknames |
| `managers` | formData | boolean | optional | Whether or not to delete managers of the location |
| `wanConfiguration` | formData | boolean | optional | Whether or not to delete wanConfiguration |

**Possible responses:** `204` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/wpsState`
*Get WPS state*

<div><strong>200</strong>: Success, a job well done.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id not found or nodeId missing from URL
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.wpsState`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/startWps`
*Start a WPS session*

<div><strong>201</strong>: Success, a WPS session was requested.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id not found or nodeId missing from URL
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.startWps`

**Required to call:** `id` (path), `locationId` (path), `nodeId` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `nodeId` | formData | string | **REQUIRED** |  |
| `keyId` | formData | string | optional |  |
| `networkId` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/appTime/appsSummary`
*Get Apptime apps and traffic class stats*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.appsSummary`

**Required to call:** `id` (path), `locationId` (path), `timePeriod` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `timePeriod` | query | string | **REQUIRED** | Any of "lastHour", "last24Hours","last7Days","last30Days" |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/appTime/appUsageSummary`
*Identify Categories and apps usage*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.appUsageSummary`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `macs` | formData | string | optional | list of macs |
| `persons` | formData | string | optional | list of person ids |
| `groups` | formData | string | optional | list of group ids |
| `apps` | formData | string | optional | list of apps |
| `appCategories` | formData | string | optional | list of app categories |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/appTime/appUsageSummary/deviceTime`
*Get average device time minutes*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.appUsageDeviceTimeMinutes`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `macs` | formData | string | optional | list of macs |
| `persons` | formData | string | optional | list of person ids |
| `groups` | formData | string | optional | list of group ids |
| `apps` | formData | string | optional | list of apps |
| `appCategories` | formData | string | optional | list of app categories |
| `type` | formData | string | optional | Average device time usage type - daily or weekly. Default daily |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/appTime/deviceTimeSummary`
*Get persons & groups device time summary for last 7 days*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDeviceTimeSummary`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/appTime/networkTimeUsage`
*Get Network time usage stats of associated devices. Default - all devices in location*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getNetworkTimeUsage`

**Required to call:** `id` (path), `locationId` (path), `timePeriod` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `timePeriod` | formData | string | **REQUIRED** | Any of last24Hours,last7Days,last30Days,last90Days |
| `persons` | formData | string | optional | person-ids |
| `groups` | formData | string | optional | group-ids |
| `macs` | formData | string | optional | mac addresses of devices |
| `applyAppsDisplayFilter` | formData | boolean | optional |  |
| `includeContentCategories` | formData | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/appTime/networkDataUsage`
*Get Network data usage stats of associated devices. Default - all devices in location*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getNetworkDataUsage`

**Required to call:** `id` (path), `locationId` (path), `timePeriod` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `timePeriod` | formData | string | **REQUIRED** | Any of last24Hours,last7Days,last30Days,last90Days |
| `persons` | formData | string | optional | person-ids |
| `groups` | formData | string | optional | group-ids |
| `macs` | formData | string | optional | mac addresses of devices |
| `applyAppsDisplayFilter` | formData | boolean | optional |  |
| `includeContentCategories` | formData | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/appTime`
*Get a Location's AppTime config by location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getLocationAppTime`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/appTime`
*Update a Location's AppTime config by location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchLocationAppTime`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `enable` | formData | boolean | optional |  |
| `appliesToAllDevices` | formData | boolean | optional |  |
| `sandboxSizeMb` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/groups/{groupId}/appTime`
*Update a Person's AppTime config by location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or group id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchLocationDeviceGroupAppTime`

**Required to call:** `id` (path), `locationId` (path), `groupId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `groupId` | path | string | **REQUIRED** |  |
| `enable` | formData | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/persons/{personId}/appTime`
*Update a Person's AppTime config by location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or person does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchPersonAppTime`

**Required to call:** `id` (path), `locationId` (path), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |
| `enable` | formData | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/devices/{mac}/appTime`
*Update a Device's AppTime config by location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or device does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchDeviceAppTime`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `enable` | formData | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/appTime/ipFlows`
*Get IP flows config*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or device does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getAppTimeIpFlows`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/appTime/ipFlows`
*Patch IP flows config*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or device does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchAppTimeIpFlow`

**Required to call:** `id` (path), `locationId` (path), `enable` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `enable` | formData | boolean | **REQUIRED** |  |
| `expiresAt` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/appTime/categories/dataUsage`
*Fetch the AppTime Categories Data Usage Stats for a Device.*

<div><strong>200</strong>: Success, AppTime Stats returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or device does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDeviceAppTimeCategoriesDataUsage`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `timePeriod` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `timePeriod` | query | string | **REQUIRED** | Any of "weekly","dailyToday","dailyYesterday","daily2DaysAgo","daily3DaysAgo","daily4DaysAgo","daily5DaysAgo","daily6DaysAgo","last30Days","last12Months" |
| `limit` | query | number | optional | Maximum number of categories to return. Defaults to 20 |
| `grouping` | query | string | optional | typing of Grouping for the purposes of applying the limit. Can be: 'overall'\|'perTimeSlot' |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/appTime/categories/onlineTime`
*Fetch the AppTime Categories Online Time Stats for a Device.*

<div><strong>200</strong>: Success, AppTime Stats returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or device does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDeviceAppTimeCategoriesOnlineTime`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `timePeriod` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `timePeriod` | query | string | **REQUIRED** | Any of "weekly","dailyToday","dailyYesterday","daily2DaysAgo","daily3DaysAgo","daily4DaysAgo","daily5DaysAgo","daily6DaysAgo","last30Days","last12Months" |
| `limit` | query | number | optional | Maximum number of categories to return. Defaults to 20 |
| `grouping` | query | string | optional | typing of Grouping for the purposes of applying the limit. Can be: 'overall'\|'perTimeSlot' |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/appTime/apps/dataUsage`
*Fetch the AppTime Apps Data Usage Stats for a Device.*

<div><strong>200</strong>: Success, AppTime Stats returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or device does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDeviceAppTimeAppsDataUsage`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `timePeriod` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `timePeriod` | query | string | **REQUIRED** | Any of "weekly","dailyToday","dailyYesterday","daily2DaysAgo","daily3DaysAgo","daily4DaysAgo","daily5DaysAgo","daily6DaysAgo","last30Days","last12Months" |
| `limit` | query | number | optional | Maximum number of apps to return. Defaults to 20 |
| `grouping` | query | string | optional | typing of Grouping for the purposes of applying the limit. Can be: 'perTimeSlot' ONLY |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/appTime/apps/onlineTime`
*Fetch the AppTime Apps Online Time Stats for a Device.*

<div><strong>200</strong>: Success, AppTime Stats returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or device does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDeviceAppTimeAppsOnlineTime`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `timePeriod` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `timePeriod` | query | string | **REQUIRED** | Any of "weekly","dailyToday","dailyYesterday","daily2DaysAgo","daily3DaysAgo","daily4DaysAgo","daily5DaysAgo","daily6DaysAgo","last30Days","last12Months" |
| `limit` | query | number | optional | Maximum number of apps to return. Defaults to 20 |
| `grouping` | query | string | optional | typing of Grouping for the purposes of applying the limit. Can be: 'perTimeSlot' ONLY |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/persons/{personId}/appTime/categories/dataUsage`
*Fetch the AppTime Categories Data Usage Stats for a Person.*

<div><strong>200</strong>: Success, AppTime Stats returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or person does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getPersonAppTimeCategoriesDataUsage`

**Required to call:** `id` (path), `locationId` (path), `personId` (path), `timePeriod` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |
| `timePeriod` | query | string | **REQUIRED** | Any of "weekly","dailyToday","dailyYesterday","daily2DaysAgo","daily3DaysAgo","daily4DaysAgo","daily5DaysAgo","daily6DaysAgo","last30Days","last12Months" |
| `limit` | query | number | optional | Maximum number of categories to return. Defaults to 20 |
| `grouping` | query | string | optional | typing of Grouping for the purposes of applying the limit. Can be: 'overall'\|'perTimeSlot' |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/persons/{personId}/appTime/categories/onlineTime`
*Fetch the AppTime Categories Online Time Stats for a Person.*

<div><strong>200</strong>: Success, AppTime Stats returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or person does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getPersonAppTimeCategoriesOnlineTime`

**Required to call:** `id` (path), `locationId` (path), `personId` (path), `timePeriod` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |
| `timePeriod` | query | string | **REQUIRED** | Any of "weekly","dailyToday","dailyYesterday","daily2DaysAgo","daily3DaysAgo","daily4DaysAgo","daily5DaysAgo","daily6DaysAgo","last30Days","last12Months" |
| `limit` | query | number | optional | Maximum number of categories to return. Defaults to 20 |
| `grouping` | query | string | optional | typing of Grouping for the purposes of applying the limit. Can be: 'overall'\|'perTimeSlot' |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/persons/{personId}/appTime/apps/dataUsage`
*Fetch the AppTime Apps Data Usage Stats for a Person.*

<div><strong>200</strong>: Success, AppTime Stats returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or person does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getPersonAppTimeAppsDataUsage`

**Required to call:** `id` (path), `locationId` (path), `personId` (path), `timePeriod` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |
| `timePeriod` | query | string | **REQUIRED** | Any of "weekly","dailyToday","dailyYesterday","daily2DaysAgo","daily3DaysAgo","daily4DaysAgo","daily5DaysAgo","daily6DaysAgo","last30Days","last12Months" |
| `limit` | query | number | optional | Maximum number of apps to return. Defaults to 20 |
| `grouping` | query | string | optional | typing of Grouping for the purposes of applying the limit. Can be: 'perTimeSlot' ONLY |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/persons/{personId}/appTime/apps/onlineTime`
*Fetch the AppTime Apps Online Time Stats for a Person.*

<div><strong>200</strong>: Success, AppTime Stats returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or person does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getPersonAppTimeAppsOnlineTime`

**Required to call:** `id` (path), `locationId` (path), `personId` (path), `timePeriod` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |
| `timePeriod` | query | string | **REQUIRED** | Any of "weekly","dailyToday","dailyYesterday","daily2DaysAgo","daily3DaysAgo","daily4DaysAgo","daily5DaysAgo","daily6DaysAgo","last30Days","last12Months" |
| `limit` | query | number | optional | Maximum number of apps to return. Defaults to 20 |
| `grouping` | query | string | optional | typing of Grouping for the purposes of applying the limit. Can be: 'perTimeSlot' ONLY |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/{networkId}/appTime/categories/dataUsage`
*Fetch the AppTime Categories Data Usage Stats for captivePortal network.*

<div><strong>200</strong>: Success, AppTime Stats returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or secondary networks does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getGuestNetworkAppTimeCategoriesDataUsage`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `timePeriod` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `timePeriod` | query | string | **REQUIRED** | Any of "weekly","dailyToday","dailyYesterday","daily2DaysAgo","daily3DaysAgo","daily4DaysAgo","daily5DaysAgo","daily6DaysAgo","last30Days","last12Months" |
| `limit` | query | number | optional | Maximum number of categories to return. Defaults to 20 |
| `grouping` | query | string | optional | typing of Grouping for the purposes of applying the limit. Can be: 'overall'\|'perTimeSlot' |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/{networkId}/appTime/categories/onlineTime`
*Fetch the AppTime Categories Online Time Stats for captivePortal network.*

<div><strong>200</strong>: Success, AppTime Stats returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or secondary networks does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getGuestNetworkAppTimeCategoriesOnlineTime`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `timePeriod` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `timePeriod` | query | string | **REQUIRED** | Any of "weekly","dailyToday","dailyYesterday","daily2DaysAgo","daily3DaysAgo","daily4DaysAgo","daily5DaysAgo","daily6DaysAgo","last30Days","last12Months" |
| `limit` | query | number | optional | Maximum number of categories to return. Defaults to 20 |
| `grouping` | query | string | optional | typing of Grouping for the purposes of applying the limit. Can be: 'overall'\|'perTimeSlot' |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/{networkId}/appTime/apps/dataUsage`
*Fetch the AppTime Apps Data Usage Stats for captivePortal network.*

<div><strong>200</strong>: Success, AppTime Stats returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or secondary networks does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getGuestNetworkAppTimeAppsDataUsage`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `timePeriod` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `timePeriod` | query | string | **REQUIRED** | Any of "weekly","dailyToday","dailyYesterday","daily2DaysAgo","daily3DaysAgo","daily4DaysAgo","daily5DaysAgo","daily6DaysAgo","last30Days","last12Months" |
| `limit` | query | number | optional | Maximum number of apps to return. Defaults to 20 |
| `grouping` | query | string | optional | typing of Grouping for the purposes of applying the limit. Can be: 'perTimeSlot' ONLY |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortals/{networkId}/appTime/apps/onlineTime`
*Fetch the AppTime Apps Online Time Stats for captivePortal network.*

<div><strong>200</strong>: Success, AppTime Stats returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or secondary networks does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getGuestNetworkAppTimeAppsOnlineTime`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `timePeriod` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `timePeriod` | query | string | **REQUIRED** | Any of "weekly","dailyToday","dailyYesterday","daily2DaysAgo","daily3DaysAgo","daily4DaysAgo","daily5DaysAgo","daily6DaysAgo","last30Days","last12Months" |
| `limit` | query | number | optional | Maximum number of apps to return. Defaults to 20 |
| `grouping` | query | string | optional | typing of Grouping for the purposes of applying the limit. Can be: 'perTimeSlot' ONLY |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/secondaryNetworks/fronthauls/{networkId}/appTime/categories/dataUsage`
*Fetch the AppTime Categories Data Usage Stats for fronthaul network.*

<div><strong>200</strong>: Success, AppTime Stats returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or secondary networks does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getEmployeeNetworkAppTimeCategoriesDataUsage`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `timePeriod` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `timePeriod` | query | string | **REQUIRED** | Any of "weekly","dailyToday","dailyYesterday","daily2DaysAgo","daily3DaysAgo","daily4DaysAgo","daily5DaysAgo","daily6DaysAgo","last30Days","last12Months" |
| `limit` | query | number | optional | Maximum number of categories to return. Defaults to 20 |
| `grouping` | query | string | optional | typing of Grouping for the purposes of applying the limit. Can be: 'overall'\|'perTimeSlot' |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/secondaryNetworks/fronthauls/{networkId}/appTime/categories/onlineTime`
*Fetch the AppTime Categories Online Time Stats for fronthaul network.*

<div><strong>200</strong>: Success, AppTime Stats returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or secondary networks does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getEmployeeNetworkAppTimeCategoriesOnlineTime`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `timePeriod` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `timePeriod` | query | string | **REQUIRED** | Any of "weekly","dailyToday","dailyYesterday","daily2DaysAgo","daily3DaysAgo","daily4DaysAgo","daily5DaysAgo","daily6DaysAgo","last30Days","last12Months" |
| `limit` | query | number | optional | Maximum number of categories to return. Defaults to 20 |
| `grouping` | query | string | optional | typing of Grouping for the purposes of applying the limit. Can be: 'overall'\|'perTimeSlot' |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/secondaryNetworks/fronthauls/{networkId}/appTime/apps/dataUsage`
*Fetch the AppTime Apps Data Usage Stats for fronthaul network.*

<div><strong>200</strong>: Success, AppTime Stats returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or secondary networks does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getEmployeeNetworkAppTimeAppsDataUsage`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `timePeriod` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `timePeriod` | query | string | **REQUIRED** | Any of "weekly","dailyToday","dailyYesterday","daily2DaysAgo","daily3DaysAgo","daily4DaysAgo","daily5DaysAgo","daily6DaysAgo","last30Days","last12Months" |
| `limit` | query | number | optional | Maximum number of apps to return. Defaults to 20 |
| `grouping` | query | string | optional | typing of Grouping for the purposes of applying the limit. Can be: 'perTimeSlot' ONLY |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/secondaryNetworks/fronthauls/{networkId}/appTime/apps/onlineTime`
*Fetch the AppTime Apps Online Time Stats for fronthaul network.*

<div><strong>200</strong>: Success, AppTime Stats returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or secondary networks does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getEmployeeNetworkAppTimeAppsOnlineTime`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `timePeriod` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `timePeriod` | query | string | **REQUIRED** | Any of "weekly","dailyToday","dailyYesterday","daily2DaysAgo","daily3DaysAgo","daily4DaysAgo","daily5DaysAgo","daily6DaysAgo","last30Days","last12Months" |
| `limit` | query | number | optional | Maximum number of apps to return. Defaults to 20 |
| `grouping` | query | string | optional | typing of Grouping for the purposes of applying the limit. Can be: 'perTimeSlot' ONLY |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/networks/{networkId}/gdprData`
*Fetch the Gdpr Captive Portals data for a guest.*

<div><strong>200</strong>: Success, GDPR Captive Portals data returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or secondary networks does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getGdprCaptivePortalsData`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `email` (query), `localEndDate` (query), `localStartDate` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `email` | query | string | **REQUIRED** |  |
| `localEndDate` | query | string | **REQUIRED** |  |
| `localStartDate` | query | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/secondaryNetworks/captivePortal/{networkId}/gdprForget/guests`
*Delete the Gdpr Captive Portals data for a guest.*

<div><strong>200</strong>: Success, GDPR Captive Portals data deleted.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or secondary networks does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteGdprCaptivePortalsData`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `data` | body | GuestCaptivePortalGdprForgetDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/wifiNetwork/appTime/categories/dataUsage`
*Fetch the AppTime Categories Data Usage Stats for captivePortal network.*

<div><strong>200</strong>: Success, AppTime Stats returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or secondary networks does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDefaultNetworkAppTimeCategoriesDataUsage`

**Required to call:** `id` (path), `locationId` (path), `timePeriod` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `timePeriod` | query | string | **REQUIRED** | Any of "weekly","dailyToday","dailyYesterday","daily2DaysAgo","daily3DaysAgo","daily4DaysAgo","daily5DaysAgo","daily6DaysAgo","last30Days","last12Months" |
| `limit` | query | number | optional | Maximum number of categories to return. Defaults to 20 |
| `grouping` | query | string | optional | typing of Grouping for the purposes of applying the limit. Can be: 'overall'\|'perTimeSlot' |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/wifiNetwork/appTime/categories/onlineTime`
*Fetch the AppTime Categories Online Time Stats for captivePortal network.*

<div><strong>200</strong>: Success, AppTime Stats returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or secondary networks does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDefaultNetworkAppTimeCategoriesOnlineTime`

**Required to call:** `id` (path), `locationId` (path), `timePeriod` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `timePeriod` | query | string | **REQUIRED** | Any of "weekly","dailyToday","dailyYesterday","daily2DaysAgo","daily3DaysAgo","daily4DaysAgo","daily5DaysAgo","daily6DaysAgo","last30Days","last12Months" |
| `limit` | query | number | optional | Maximum number of categories to return. Defaults to 20 |
| `grouping` | query | string | optional | typing of Grouping for the purposes of applying the limit. Can be: 'overall'\|'perTimeSlot' |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/wifiNetwork/appTime/apps/dataUsage`
*Fetch the AppTime Apps Data Usage Stats for captivePortal network.*

<div><strong>200</strong>: Success, AppTime Stats returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or secondary networks does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDefaultNetworkAppTimeAppsDataUsage`

**Required to call:** `id` (path), `locationId` (path), `timePeriod` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `timePeriod` | query | string | **REQUIRED** | Any of "weekly","dailyToday","dailyYesterday","daily2DaysAgo","daily3DaysAgo","daily4DaysAgo","daily5DaysAgo","daily6DaysAgo","last30Days","last12Months" |
| `limit` | query | number | optional | Maximum number of apps to return. Defaults to 20 |
| `grouping` | query | string | optional | typing of Grouping for the purposes of applying the limit. Can be: 'perTimeSlot' ONLY |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/wifiNetwork/appTime/apps/onlineTime`
*Fetch the AppTime Apps Online Time Stats for default network.*

<div><strong>200</strong>: Success, AppTime Stats returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or secondary networks does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDefaultNetworkAppTimeAppsOnlineTime`

**Required to call:** `id` (path), `locationId` (path), `timePeriod` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `timePeriod` | query | string | **REQUIRED** | Any of "weekly","dailyToday","dailyYesterday","daily2DaysAgo","daily3DaysAgo","daily4DaysAgo","daily5DaysAgo","daily6DaysAgo","last30Days","last12Months" |
| `limit` | query | number | optional | Maximum number of apps to return. Defaults to 20 |
| `grouping` | query | string | optional | typing of Grouping for the purposes of applying the limit. Can be: 'perTimeSlot' ONLY |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/rooms`
*Get a Location's Rooms config by location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getLocationRooms`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/rooms`
*Create a Room for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist and is not known to Plume</div>
<div><strong>422</strong>: Devices and Nodes must be defined and mac addresses must be valid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postRooms`

**Required to call:** `id` (path), `locationId` (path), `name` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `name` | formData | string | **REQUIRED** | name of this Room |
| `devices` | formData | string | optional | mac addresses of devices assigned to this Room |
| `nodes` | formData | string | optional | nodeIds assigned to this Room |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/rooms/{roomId}`
*Delete a Room for a location ID.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or Room id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteRoom`

**Required to call:** `id` (path), `locationId` (path), `roomId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `roomId` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/rooms/{roomId}`
*Patch a Room for a Location ID/Room ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist and is not known to Plume</div>
<div><strong>422</strong>: Devices and Nodes must be defined and mac addresses must be valid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchRoom`

**Required to call:** `id` (path), `locationId` (path), `roomId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `roomId` | path | string | **REQUIRED** |  |
| `name` | formData | string | optional | name of this Room |
| `devices` | formData | string | optional | mac addresses of devices assigned to this Room |
| `nodes` | formData | string | optional | nodeIds assigned to this Room |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/createOrUpdateManager`
*Create or update manager and his Location Access*

<div><strong>200</strong>: Successfully created/updated manager and LocationAccess.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization require.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.createOrUpdateManager`

**Required to call:** `accountId` (formData), `email` (formData), `name` (formData), `access` (formData), `partnerId` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `accountId` | formData | string | **REQUIRED** | manager accountId |
| `email` | formData | string | **REQUIRED** | manager email |
| `name` | formData | string | **REQUIRED** | manager name |
| `access` | formData | string | **REQUIRED** | array of objects containing locationId and accessType |
| `partnerId` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/managers`
*Get a list of all managers the are assigned to manage your location.*

<div><strong>200</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist.</div>

operationId: `Customer.prototype.getManagersListForLocation`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/managers`
*Assign a manager to your location *

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>422</strong>: Invalid email, name, access type or manager is already assigned to this location </div>

operationId: `Customer.prototype.postManager`

**Required to call:** `id` (path), `name` (formData), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `email` | formData | string | optional |  |
| `name` | formData | string | **REQUIRED** |  |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `accessType` | formData | string | optional |  |
| `notificationOptions` | formData | string | optional |  |
| `accountId` | formData | string | optional |  |
| `partnerId` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/entitledAccess`
*Get a list of all locations on which you are assigned as a manager.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>422</strong>: Invalid email, name, access type or manager is already assigned to this location </div>

operationId: `Customer.prototype.getEntitledAccessList`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/allLocations`
*Get a list of all locations on which you are assigned as a manager with accessType and on which you are owner.*

<div><strong>200</strong>: Success.</div>
<div><strong>404</strong>: Customer does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getAllLocations`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/managers/{managerId}/resendInvite`
*Resend invite to a manager that has status "pending".*

<div><strong>204</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>404</strong>: Location or Manager does not exist.</div>
<div><strong>422</strong>: Manager already accepted the invite to manage the location </div>

operationId: `Customer.prototype.resendManagerInvite`

**Required to call:** `id` (path), `locationId` (path), `managerId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `managerId` | path | string | **REQUIRED** |  |
| `notificationOptions` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/entitledAccess/{locationId}/v2/accessTokens`
*Get a token set for a location where you are assigned as a manager.*

This endpoint is used to generate token set for a managed location
The response will contain an access token and a refresh token.

operationId: `Customer.prototype.getTokenSetForManagedLocation`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful; `403` Forbidden; `500` Unhandled API error

#### `POST` `/Customers/{id}/entitledAccess/{locationId}/accessTokens`
*Get an access token for a location where you are assigned as a manager*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>422</strong>: Invalid email, name, access type or manager is already assigned to this location </div>

operationId: `Customer.prototype.getAccessTokenForManagedLocation`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/managers/{managerId}`
*Delete manager access for location and destroy access tokens for that manager".*

<div><strong>204</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>404</strong>: Location or Manager does not exist.</div>

operationId: `Customer.prototype.deleteManagerAccess`

**Required to call:** `id` (path), `locationId` (path), `managerId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `managerId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/managers/{managerId}`
*Update type of access of manager on location.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchLocationManager`

**Required to call:** `id` (path), `locationId` (path), `managerId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `managerId` | path | string | **REQUIRED** |  |
| `accessType` | formData | string | optional |  |
| `name` | formData | string | optional |  |
| `notificationOptions` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/blePairingPin`
*Get BLE pairing pin for a node that is claimed by the selected location*

<div><strong>200</strong>: Success, pin generated.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>404</strong>: Location or node does not exist.</div>
<div><strong>422</strong>: Invalid token. </div>

operationId: `Customer.prototype.getNodeBlePairingPin`

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path), `token` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `nodeId` | path | string | **REQUIRED** |  |
| `token` | query | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/networkAccess/blocked/{mac}`
*Unblock blocked devices*

<div><strong>204</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist.</div>

operationId: `Customer.prototype.unblockDevice`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/networkAccess/blocked`
*Block devices*

<div><strong>200</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist.</div>

operationId: `Customer.prototype.blockDevices`

**Required to call:** `id` (path), `locationId` (path), `macs` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `macs` | body | array | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/networkAccess/networks/{networkId}/approved/{mac}`
*Unapprove approved devices in the network*

<div><strong>204</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>404</strong>: Network does not exist.</div>
<div><strong>404</strong>: Device is not approved.</div>

operationId: `Customer.prototype.unapproveDevice`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `mac` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/networkAccess/networks/{networkId}/approved`
*Approve devices in the network*

<div><strong>204</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>404</strong>: Network does not exist.</div>

operationId: `Customer.prototype.approveDevices`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `macs` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `macs` | body | array | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/networkAccess/networks/{networkId}`
*Enable or disable purgatory in the network*

<div><strong>204</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>404</strong>: Network does not exist.</div>

operationId: `Customer.prototype.patchNetworkAccessNetwork`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `purgatory` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `purgatory` | formData | boolean | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/networkAccess/networks`
*Get information about networkAccess networks*

<div><strong>204</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist.</div>

operationId: `Customer.prototype.getNetworkAccessNetworks`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/networkAccess/networks/{networkId}/deviceGroups`
*Get a list of device groups in a network, along with a list of member devices and group shares.*

<div><strong>200</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>404</strong>: Network does not exist.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>

operationId: `Customer.prototype.getDeviceGroups`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/networkAccess/networks/{networkId}/deviceGroups`
*Create a named device group within a network and optionally specify member devices.*

<div><strong>200</strong>: Success.</div>
<div><strong>422</strong>: Schema validation failed.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>404</strong>: Network does not exist.</div>
<div><strong>403</strong>: Not allowed to create groups in unsupported networks.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>400</strong>: Invalid JSON or missing arguments.</div>

operationId: `Customer.prototype.postDeviceGroup`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `name` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `name` | formData | string | **REQUIRED** |  |
| `devices` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/networkAccess/networks/{networkId}/deviceGroups/{groupId}`
*Delete a device group from a network.*

<div><strong>200</strong>: Success.</div>
<div><strong>422</strong>: Schema validation failed.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>404</strong>: Network does not exist.</div>
<div><strong>403</strong>: Not allowed to delete standalone groups or groups in unsupported networks.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>400</strong>: Invalid JSON or missing arguments.</div>

operationId: `Customer.prototype.deleteDeviceGroup`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `groupId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `groupId` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/networkAccess/networks/{networkId}/deviceGroups/{groupId}`
*Change a device group name or device members.*

<div><strong>200</strong>: Success.</div>
<div><strong>422</strong>: Schema validation failed.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>404</strong>: Network does not exist.</div>
<div><strong>403</strong>: Not allowed to modify standalone groups or groups in unsupported networks.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>400</strong>: Invalid JSON or missing arguments.</div>

operationId: `Customer.prototype.patchDeviceGroup`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `groupId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `groupId` | path | string | **REQUIRED** |  |
| `name` | formData | string | optional |  |
| `devices` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/networkAccess/networks/{networkId}/deviceGroups/{groupId}/groupShares`
*Share access for a group or employee.*

<p>This endpoint allows for a device in the first network to have access to all of the devices in the other group in the second network and/or to individual devices in the second network. In other words, by sharing access, we're allowing a single device to communicate with other devices across networks, by specifying other groups and/or individual devices.</p>
<div><strong>200</strong>: Success.</div>
<div><strong>422</strong>: Schema validation failed.</div>
<div><strong>422</strong>: Illegal share.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>404</strong>: Network does not exist.</div>
<div><strong>404</strong>: Group does not exist.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>400</strong>: Invalid JSON or missing arguments.</div>

operationId: `Customer.prototype.shareDeviceGroup`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `groupId` (path), `groups` (formData), `devices` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `groupId` | path | string | **REQUIRED** |  |
| `groups` | formData | string | **REQUIRED** |  |
| `devices` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/networkAccess/networks/{networkId}/devices/{mac}/groupShares`
*Share access to individual device. *

<p>This endpoint allows for a device in the first network to have access to all of the devices in the other group in the second network and/or to individual devices in the second network. In other words, by sharing access, we're allowing a single device to communicate with other devices across networks, by specifying other groups and/or individual devices.</p>
<div><strong>200</strong>: Success.</div>
<div><strong>422</strong>: Schema validation failed.</div>
<div><strong>422</strong>: Illegal share.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>404</strong>: Network does not exist.</div>
<div><strong>404</strong>: Group does not exist.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>400</strong>: Invalid JSON or missing arguments.</div>

operationId: `Customer.prototype.shareDevice`

**Required to call:** `id` (path), `locationId` (path), `networkId` (path), `mac` (path), `groups` (formData), `devices` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `networkId` | path | string | **REQUIRED** |  |
| `mac` | path | string | **REQUIRED** |  |
| `groups` | formData | string | **REQUIRED** |  |
| `devices` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/publishSlowChangingDimensionConfigs`
*Publish all slow changing dimension Kafka messages*

<div><strong>204</strong>: Success.</div>

operationId: `Customer.prototype.publishSlowChangingDimensionConfigs`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/devices/{mac}/qos`
*Set QoS of a single device*

<div><strong>202</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>422</strong>: Prioritization is not a valid value.</div>

operationId: `Customer.prototype.postDeviceQos`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `prioritization` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `prioritization` | formData | string | **REQUIRED** |  |

**Possible responses:** `202` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/devices/{mac}/qos`
*Update QoS of a single device*

<div><strong>202</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>422</strong>: Prioritization is not a valid value.</div>

operationId: `Customer.prototype.patchDeviceQos`

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `prioritization` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `prioritization` | formData | string | **REQUIRED** |  |

**Possible responses:** `202` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/devices/{mac}/qos/prioritization`
*Delete prioritization of a single device*

<div><strong>202</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist.</div>

operationId: `Customer.prototype.deleteDeviceQosPrioritization`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/devices/stitch`
*Delete prioritization of a single device*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>400</strong>: Missing oldMac or newMac field.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>422</strong>: oldMac or newMac is not valid mac.</div>
<div><strong>422</strong>: If oldMac and newMac are the same.</div>

operationId: `Customer.prototype.stitchDevice`

**Required to call:** `id` (path), `locationId` (path), `oldMac` (formData), `newMac` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `oldMac` | formData | string | **REQUIRED** |  |
| `newMac` | formData | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `POST` `/Customers/import`
*Import customer data*

<div><strong>204</strong>: Success.</div>
<div><strong>400</strong>: Nothing to import.</div>
<div><strong>422</strong>: Import data is invalid.</div>

operationId: `Customer.importData`

**Required to call:** `data` (formData), `migratedFrom` (formData), `reason` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `data` | formData | string | **REQUIRED** |  |
| `migratedFrom` | formData | string | **REQUIRED** |  |
| `reason` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/import/overlordAndCouncilman`
*Import customer data*

<div><strong>204</strong>: Success.</div>
<div><strong>400</strong>: Nothing to import.</div>

operationId: `Customer.importOverlordAndCouncilmanData`

**Required to call:** `body` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `body` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/dpp`
*Get the current DPP configuration for a Location ID.*

<div><strong>200</strong>: Success, current DPP configuration returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDpp`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/dpp`
*Patch the DPP configuration mode for a Location ID.*

<div><strong>202</strong>: Success, DPP updated.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>422</strong>: DPP value is invalid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchDpp`

**Required to call:** `id` (path), `locationId` (path), `mode` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mode` | formData | string | **REQUIRED** | auto \|\| enable \|\| disable |

**Possible responses:** `202` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/wifiNetwork/dpp`
*Get the current DPP configurator for a Location ID.*

<div><strong>200</strong>: Success, current DPP configurator returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getWifiNetworkDpp`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/wifiNetwork/dpp`
*Create the DPP setting for a Location ID.*

<div><strong>202</strong>: Success, new DPP configurator generated.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postWifiNetworkDpp`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `enabled` | formData | boolean | optional | should we configure dpp for this network - defaults to true |
| `curve` | formData | string | optional | one of predefined elliptic curves, - optional,  if missing in request default to prime256v1 |
| `privateKey` | formData | string | optional | privateKey, must also provide public part if present, optional |
| `publicKey` | formData | string | optional | publicKey |

**Possible responses:** `202` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/wifiNetwork/dpp/bootstrapUris`
*Create a bootstrap for DPP setting for a wifi network.*

<div><strong>200</strong>: Success, new DPP configurator generated.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or wifi network does not exist.</div>
<div><strong>422</strong>: Invalid curve.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postWifiNetworkDppBootstrap`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `curve` | formData | string | optional | one of predefined elliptic curves, - optional,  if missing in requset default to prime256v1 |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/wifiNetwork/dpp/enrollments`
*Create an enrollment for DPP setting for a wifi network.*

<div><strong>202</strong>: Success, new DPP configurator generated.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or wifi network does not exist.</div>
<div><strong>404</strong>: Configurator keys for network not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postWifiNetworkDppEnrollment`

**Required to call:** `id` (path), `locationId` (path), `bootstrapUri` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `bootstrapUri` | formData | string | **REQUIRED** |  |

**Possible responses:** `202` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/ethernetLan`
*Updates location nodes with ethernetLan modes*

<div><strong>202</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>404</strong>: Node does not exist.</div>
<div><strong>422</strong>: nodeEthernetLan does not exist.</div>

operationId: `Customer.prototype.putEthernetLan`

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path), `nodeEthernetLan` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `nodeId` | path | string | **REQUIRED** |  |
| `nodeEthernetLan` | body | object | **REQUIRED** |  |

**Possible responses:** `202` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/sniffing`
*Get DNS, HTTP, UPnP and mDNS sniffing toggles for a Location ID.*

<div><strong>200</strong>: Success, current sniffing toggles returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getSniffing`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/sniffing`
*Updates location sniffing toggle modes*

<div><strong>202</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>404</strong>: Location does not exist.</div>

operationId: `Customer.prototype.putSniffing`

**Required to call:** `id` (path), `locationId` (path), `dns` (formData), `http` (formData), `upnp` (formData), `mdns` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `dns` | formData | string | **REQUIRED** | object with property "mode": an enum of values which include: auto, enable, disable |
| `http` | formData | string | **REQUIRED** | object with property "mode": an enum of values which include: auto, enable, disable |
| `upnp` | formData | string | **REQUIRED** | object with property "mode": an enum of values which include: auto, enable, disable |
| `mdns` | formData | string | **REQUIRED** | object with property "mode": an enum of values which include: auto, enable, disable |

**Possible responses:** `202` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/flowStats`
*GET the flow stats configuration*

<div><strong>200</strong>: Success, current flow stats configuration returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getFlowStats`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/flowStats`
*Patches the flow stats configuration*

<div><strong>202</strong>: Success, your new info looks good.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id, does not exist.</div>
<div><strong>422</strong>: Input value is invalid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchFlowStats`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `iotDeviceConfig` | formData | string | optional | auto \|\| enable \|\| disable |
| `screenDeviceConfig` | formData | string | optional | auto \|\| enable \|\| disable |
| `lanIotDeviceConfig` | formData | string | optional | auto \|\| enable \|\| disable |
| `interfaceStatsConfig` | formData | string | optional | auto \|\| enable \|\| disable |

**Possible responses:** `202` Request was successful

#### `GET` `/Customers/{id}/cloud`
*Checks users migration data to provide currently active cloud details*

<div><strong>200</strong>: Success.</div>
<div><strong>404</strong>: Customer does not exist.</div>

operationId: `Customer.prototype.getActiveCloud`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/v2/configAndState`
*Gets all the configs from Overlord for a specified location.*

<div><strong>200</strong>: Success, got the data.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getLocationOverlordConfigs`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/event/forceOnboardingRadios`
*Triggers a forceOnboardingRadios one time event. Force onboarding radios for a specific duration*

<div><strong>202</strong>: Success, one time event triggered.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: Invalid data.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordTriggerForceOnboardingRadiosEvent`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `allowedRadios` | formData | string | optional | [ &nbsp;&nbsp;string ] |
| `durationSecs` | formData | integer | optional |  integer |

**Possible responses:** `202` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/event/revSsh`
*Triggers a revSsh one time event. RevSsh is used to configure a reverse SSH tunnel on a node.*

<div><strong>202</strong>: Success, one time event triggered.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: Invalid data.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordTriggerRevSshEvent`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `nodeIds` | formData | string | optional | [ &nbsp;&nbsp;string ] |
| `config` | formData | string | optional | {"serverHost": string, "serverPort": integer, "serverUser": string, "serverPubkey": [  string ], "tunnelRemoteBindAddr": string, "tunnelRemoteBindPort": integer, "tunnelLocalAddr": string, "tunnelLocalPort": integer, "idleTimeout": integer, "sessionMaxTime": integer, "nodeGenKeyType": string enum: [ NODE_GEN_KEY_TYPE_UNKNOWN, NODE_GEN_KEY_TYPE_RSA, NODE_GEN_KEY_TYPE_ECDSA, NODE_GEN_KEY_TYPE_ED25519 ], "nodeGenKeyBits": integer, "otherConfig": [" " {"key": string, "value": string } ] } |

**Possible responses:** `202` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/config/appQoe`
*Resets a appQoe config. AppQoe is to monitor the Quality of Experience of these Apps in the house, which is what this PRD covers. This QoE monitoring will allow CSPs understand likely issues with applications.*

<div><strong>202</strong>: Success, reset.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordDeleteAppQoeConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `202` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/config/appQoe`
*Updates a appQoe config. AppQoe is to monitor the Quality of Experience of these Apps in the house, which is what this PRD covers. This QoE monitoring will allow CSPs understand likely issues with applications.*

<div><strong>202</strong>: Success, accepted and forwarded the data.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: Invalid data.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordUpdateAppQoeConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mode` | formData | string | optional |  string enum: [ AUTO, ENABLE, DISABLE ] |

**Possible responses:** `202` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/config/clientSteering`
*Resets a clientSteering config. Client Steering configuration*

<div><strong>202</strong>: Success, reset.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordDeleteClientSteering`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `202` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/config/clientSteering`
*Updates a clientSteering config. Client Steering configuration*

<div><strong>202</strong>: Success, accepted and forwarded the data.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: Invalid data.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordUpdateClientSteering`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mode` | formData | string | optional |  string enum: [ AUTO, ENABLE, DISABLE ] |
| `allowMloSteering` | formData | string | optional |  string enum: [ AUTO, ENABLE, DISABLE ] |

**Possible responses:** `202` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/config/flashLogging`
*Resets a flashLogging config. Flash logging configuration, for toggling if and which flashing should be logged*

<div><strong>202</strong>: Success, reset.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordDeleteFlashLoggingConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `202` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/config/flashLogging`
*Updates a flashLogging config. Flash logging configuration, for toggling if and which flashing should be logged*

<div><strong>202</strong>: Success, accepted and forwarded the data.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: Invalid data.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordUpdateFlashLoggingConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `forceDestination` | formData | string | optional |  string enum: [ NODE_LOGGING_DESTINATION_DEFAULT, NODE_LOGGING_DESTINATION_FLASH, NODE_LOGGING_DESTINATION_FLASH_RAMOOPS, NODE_LOGGING_DESTINATION_RAMOOPS, NODE_LOGGING_DESTINATION_OFF ] |

**Possible responses:** `202` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/config/flowCache`
*Resets a flowCache config. Enable/disable Flow Cache to help support devQA to check influence on the first stage of the investigation.*

<div><strong>202</strong>: Success, reset.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordDeleteFlowCacheConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `202` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/config/flowCache`
*Updates a flowCache config. Enable/disable Flow Cache to help support devQA to check influence on the first stage of the investigation.*

<div><strong>202</strong>: Success, accepted and forwarded the data.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: Invalid data.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordUpdateFlowCacheConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `enable` | formData | boolean | optional |  boolean |

**Possible responses:** `202` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/config/puncturing`
*Resets a puncturing config. Puncturing allows to use a selective number of subchannels within a channel for PPDU transmission to WIFI 7 devices*

<div><strong>202</strong>: Success, reset.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordDeletePuncturingConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `202` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/config/puncturing`
*Updates a puncturing config. Puncturing allows to use a selective number of subchannels within a channel for PPDU transmission to WIFI 7 devices*

<div><strong>202</strong>: Success, accepted and forwarded the data.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: Invalid data.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordUpdatePuncturingConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mode` | formData | string | optional |  string enum: [ AUTO, ENABLE, DISABLE ] |

**Possible responses:** `202` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/config/qos`
*Resets a qos config. QOS configuration*

<div><strong>202</strong>: Success, reset.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordDeleteQosConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `202` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/config/qos`
*Updates a qos config. QOS configuration*

<div><strong>202</strong>: Success, accepted and forwarded the data.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: Invalid data.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordUpdateQosConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `wanUplinkAqm` | formData | string | optional |  string enum: [ AUTO, ENABLE, DISABLE ] |
| `wanDownlinkAqm` | formData | string | optional |  string enum: [ AUTO, ENABLE, DISABLE ] |
| `downloadBandwidth` | formData | string | optional | {"minBandwidth": integer, "baseBandwidth": integer, "maxBandwidth": integer } |
| `uploadBandwidth` | formData | string | optional | {"minBandwidth": integer, "baseBandwidth": integer, "maxBandwidth": integer } |

**Possible responses:** `202` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/config/samKnows`
*Resets a samKnows config. SamKnows is a provider of internet performance measurement services. They offer the SamKnows Router Agent, which supports a range of QoS and QoE performance measurements. These measurements can be executed both on an ad-hoc and scheduled basis.*

<div><strong>202</strong>: Success, reset.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordDeleteSamKnowsConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `202` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/config/samKnows`
*Updates a samKnows config. SamKnows is a provider of internet performance measurement services. They offer the SamKnows Router Agent, which supports a range of QoS and QoE performance measurements. These measurements can be executed both on an ad-hoc and scheduled basis.*

<div><strong>202</strong>: Success, accepted and forwarded the data.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: Invalid data.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordUpdateSamKnowsConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mode` | formData | string | optional |  string enum: [ AUTO, ENABLE, DISABLE ] |

**Possible responses:** `202` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/config/sipAlg`
*Resets a sipAlg config. sipAlg is an application within many routers. It inspects any VoIP traffic to prevent problems caused by firewalls and if necessary modifies the VoIP packets.*

<div><strong>202</strong>: Success, reset.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordDeleteSipAlgConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `202` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/config/sipAlg`
*Updates a sipAlg config. sipAlg is an application within many routers. It inspects any VoIP traffic to prevent problems caused by firewalls and if necessary modifies the VoIP packets.*

<div><strong>202</strong>: Success, accepted and forwarded the data.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: Invalid data.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordUpdateSipAlgConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mode` | formData | string | optional |  string enum: [ AUTO, ENABLE, DISABLE ] |

**Possible responses:** `202` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/config/stats`
*Resets a stats config. Location Stats configuration, used to toggle which stats should be collected.*

<div><strong>202</strong>: Success, reset.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordDeleteStatsConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `202` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/config/stats`
*Updates a stats config. Location Stats configuration, used to toggle which stats should be collected.*

<div><strong>202</strong>: Success, accepted and forwarded the data.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: Invalid data.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordUpdateStatsConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `offChannelScan24` | formData | string | optional |  string enum: [ AUTO, ENABLE, DISABLE ] |
| `offChannelScan50` | formData | string | optional |  string enum: [ AUTO, ENABLE, DISABLE ] |
| `offChannelScan60` | formData | string | optional |  string enum: [ AUTO, ENABLE, DISABLE ] |
| `clientAuthFails` | formData | string | optional |  string enum: [ AUTO, ENABLE, DISABLE ] |
| `lanLatency` | formData | string | optional |  string enum: [ AUTO, ENABLE, DISABLE ] |
| `wanLatency` | formData | string | optional |  string enum: [ AUTO, ENABLE, DISABLE ] |

**Possible responses:** `202` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/config/thread`
*Resets a thread config. Thread configuration, for toggling if threading is being used*

<div><strong>202</strong>: Success, reset.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordDeleteThreadConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `202` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/config/thread`
*Updates a thread config. Thread configuration, for toggling if threading is being used*

<div><strong>202</strong>: Success, accepted and forwarded the data.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: Invalid data.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordUpdateThreadConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `enable` | formData | boolean | optional |  boolean |
| `threadInterface` | formData | string | optional |  string |
| `networkInterface` | formData | string | optional |  string |
| `dataset` | formData | string | optional |  string |
| `networkName` | formData | string | optional |  string |
| `panId` | formData | number | optional |  number |
| `extPanId` | formData | string | optional |  string |
| `networkKey` | formData | string | optional |  string |
| `meshLocalPrefix` | formData | string | optional |  string |
| `channel` | formData | number | optional |  number |
| `channelMask` | formData | number | optional |  number |
| `commissioningPsk` | formData | string | optional |  string |
| `reportingInterval` | formData | number | optional |  number |

**Possible responses:** `202` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/config/unii`
*Resets a unii config. UNII configuration*

<div><strong>202</strong>: Success, reset.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordDeleteUniiConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `202` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/config/unii`
*Updates a unii config. UNII configuration*

<div><strong>202</strong>: Success, accepted and forwarded the data.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: Invalid data.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordUpdateUniiConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `unii4Mode` | formData | string | optional |  string enum: [ AUTO, ENABLE, DISABLE ] |

**Possible responses:** `202` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/config/wag`
*Resets a wag config. WAG configuration*

<div><strong>202</strong>: Success, reset.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordDeleteWagConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `202` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/config/wag`
*Updates a wag config. WAG configuration*

<div><strong>202</strong>: Success, accepted and forwarded the data.</div>
<div><strong>400</strong>: Required fields missing.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: Invalid data.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.overlordUpdateWagConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mode` | formData | string | optional |  string enum: [ AUTO, ENABLE, DISABLE ] |
| `tunnelConfig` | formData | string | optional | {"remoteEndpoint": string, "networkId": string, "routes": [  string ], "key": string, "preferredIpv6": boolean, "healthCheck": {"remoteEndpoint": string, "interval": integer, "timeout": integer } } |

**Possible responses:** `202` Request was successful

#### `POST` `/Customers/{id}/migrate`
*Migrate a customer to a different cloud.*

operationId: `Customer.prototype.migrate`

**Required to call:** `id` (path), `cloud` (formData), `migrationName` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `cloud` | formData | string | **REQUIRED** |  |
| `migrationName` | formData | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `POST` `/Customers/{id}/rollback`
*Rollback a customer to original server and delete customer on migrated server.*

<div><strong>204</strong>: Success</div>
<div><strong>400</strong>: Customer was not migrated</div>
<div><strong>400</strong>: Customer does not belong to partner</div>
<div><strong>400</strong>: Customer was not migrated to cloud</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.rollback`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |

**Possible responses:** `204` Request was successful

#### `GET` `/Customers/{id}/migration`
*Returns cloud migration status for customer*

<div><strong>200</strong>: Success, return the search result.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Customer does not exist.</div>

operationId: `Customer.prototype.migrationStatus`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/primarySecondaryNetworks`
*Get networks for wpa3 transition flow*

<div><strong>200</strong>: Success, returns the data</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id or wifiNetwork does not exist</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getPrimarySecondaryNetworks`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/primarySecondaryNetworks`
*Set networks at wpa3 transition flow*

<div><strong>202</strong>: Success, accepted the data</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist</div>
<div><strong>422</strong>: Input validation failed.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.setPrimarySecondaryNetworks`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `wpa3ssid` | formData | string | optional |  |
| `wpa3encryptionKey` | formData | string | optional |  |
| `wpa3enabled` | formData | boolean | optional |  |
| `wpa2ssid` | formData | string | optional |  |
| `wpa2enabled` | formData | boolean | optional |  |
| `wpa3CMode` | formData | string | optional | wpa3CMode can be set to "sae-compat" or "sae-compat-relaxed" |

**Possible responses:** `202` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/primarySecondaryNetworks/wpa3ssid/invitations`
*Update home devices visible to guests.*

<div><strong>200</strong>: Success, Invitation returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Customer id, location id</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getSecondaryNetworkInvitation`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/overlord/resync`
*Push all relevant location Configurations to Overlord.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putOverlordResync`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `204` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/groupOfUnassignedDevices/freeze/suspend`
*PUT GroupOfUnassignedDevices suspend for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.putGroupOfUnassignedDevicesFreezeSuspend`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/groupOfUnassignedDevices/freeze/suspend`
*Delete GroupOfUnassignedDevices suspend for a Location ID.*

<div><strong>204</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.deleteGroupOfUnassignedDevicesFreezeSuspend`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `204` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/groupOfUnassignedDevices/freeze/forever`
*PUT GroupOfUnassignedDevices forever for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.putGroupOfUnassignedDevicesFreezeForever`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/groupOfUnassignedDevices/freeze/forever`
*Delete GroupOfUnassignedDevices forever freeze for a Location ID.*

<div><strong>204</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.deleteGroupOfUnassignedDevicesFreezeForever`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `204` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/groupOfUnassignedDevices/freeze/{freezeTemplateId}`
*POST GroupOfUnassignedDevices to be frozen for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>404</strong>: Freeze Template Id not found.</div>
<div><strong>409</strong>: Freeze Template Id already applied.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.postGroupOfUnassignedDevicesFreezeTemplateId`

**Required to call:** `id` (path), `locationId` (path), `freezeTemplateId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `freezeTemplateId` | path | string | **REQUIRED** | Valid templates are uuids |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/groupOfUnassignedDevices/freeze/{freezeTemplateId}`
*Delete GroupOfUnassignedDevices uuid freeze for a Location ID.*

<div><strong>204</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.deleteGroupOfUnassignedDevicesFreezeTemplateId`

**Required to call:** `id` (path), `locationId` (path), `freezeTemplateId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `freezeTemplateId` | path | string | **REQUIRED** | Valid templates are uuids |

**Possible responses:** `204` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/groupOfUnassignedDevices/freezes`
*Delete All GroupOfUnassignedDevices freeze except autoExpire for a Location ID.*

<div><strong>204</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.deleteGroupOfUnassignedDevicesFreezes`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `204` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/groupOfUnassignedDevices/freeze/autoExpire`
*Put GroupOfUnassignedDevices autoExpire freeze for a Location ID.*

<div><strong>200</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.putGroupOfUnassignedDevicesFreezeAutoExpire`

**Required to call:** `id` (path), `locationId` (path), `expiresAt` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `expiresAt` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/groupOfUnassignedDevices/freeze/autoExpire`
*Delete GroupOfUnassignedDevices autoExpire freeze for a Location ID.*

<div><strong>204</strong>: Success, updated.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.deleteGroupOfUnassignedDevicesFreezeAutoExpire`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `204` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/groupOfUnassignedDevices/freezePolicy`
*Get GroupOfUnassignedDevices freeze policy for a Location ID.*

<div><strong>200</strong>: Ok.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>
<div><strong>501</strong>: Not Implemented if location is utilizing focuses.</div>

operationId: `Customer.prototype.getGroupOfUnassignedDevicesFreezePolicy`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/disable`
*Disable customer from logging in until their account is reactivated.*

<div><strong>204</strong>: Customer has been disabled.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Customer does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.disableLogin`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `triggerReset` | formData | boolean | optional |  |

**Possible responses:** `204` Request was successful

#### `PUT` `/Customers/{id}/enable`
*Enable customer log in, after it has been disabled.*

<div><strong>204</strong>: Customer has been enabled.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Customer does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.enableLogin`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |

**Possible responses:** `204` Request was successful

#### `GET` `/Customers/{id}/auditTrail`
*Get audit trail for a customer.*

<div><strong>200</strong>: Ok.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Customer id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getAuditTrailForCustomer`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/auditTrail`
*Get audit trail for location.*

<div><strong>200</strong>: Ok.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getAuditTrailForLocation`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/fastInterference`
*Get from Controller Fast interference status.*

<div><strong>200</strong>: Ok.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getFastInterference`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/flex/devices/{mac}/qoeMetrics`
*Device or pod QoE 15 minutes data.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDeviceQoeMetrics`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** | device mac address |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number | optional | X # of days/hours/minutes |
| `timestampISOFormat` | query | boolean | optional | either timestamp utc number or ISO string |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/flex/devices/{mac}/qoeMetricsV2`
*Device or pod QoE 15 minutes data with MLO support.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDeviceQoeMetricsV2`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** | device mac address |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number | optional | X # of days/hours/minutes |
| `timestampISOFormat` | query | boolean | optional | either timestamp utc number or ISO string |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/flex/devices/{mac}/clientSteeringStats`
*Device client steering stats with all nodes for a particular MAC address.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDeviceClientSteeringStats`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** | mac id of device |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number | optional | X # of days/hours/minutes |
| `start` | query | number | optional | number of milliseconds elapsed since 1 January 1970 00:00:00 UTC. Defaults to now - (limit * granularity) |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/flex/devices/{mac}/bandSteeringStats`
*Device band steering stats with all nodes for a particular MAC address.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDeviceBandSteeringStats`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** | mac id of device |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number | optional | X # of days/hours/minutes |
| `start` | query | number | optional | number of milliseconds elapsed since 1 January 1970 00:00:00 UTC. Defaults to now - (limit * granularity) |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/flex/devices/{mac}/clientSteeringTriggers`
*Find all instances of the model.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDeviceSteeringWithAthena`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |
| `order` | query | string | optional | desc \|\| asc |
| `limit` | query | number | optional | 1000 max for deep:false and 10 max for deep:true |
| `startAt` | query | string | optional | find objects after this value |
| `endAt` | query | string | optional | find objects before this value |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/flex/devices/{mac}/qoe/liveModeStream`
*Device or pod QoE live mode data.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getQoe1Minute`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** | mac address or pod id |
| `startTime` | query | number | optional | start timestamp |
| `timestampISOFormat` | query | boolean | optional | either timestamp utc number or ISO string |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/flex/devices/{mac}/qoe/superLiveModeStream`
*Device or pod QoE super live mode data.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getQoeSeconds`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** | mac address or pod id |
| `startTime` | query | number | optional | start timestamp |
| `timestampISOFormat` | query | boolean | optional | either timestamp utc number or ISO string |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/flex/qoe`
*Get QoE recent 1 minute data for a whole location.*

operationId: `Customer.prototype.getLocationQoe`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/flex/devices/{mac}/alarms`
*Device alarm history graph array for a particular MAC address.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDeviceAlarms`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** | mac id of device |
| `coverageAlarmThreshold` | query | string | optional | a coverage alarm will be returned (value=1) when rssi_alarm_penalty_count >= this value |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number | optional | X # of days/hours/minutes |
| `start` | query | number | optional | number of milliseconds elapsed since 1 January 1970 00:00:00 UTC. Defaults to now - (limit * granularity) |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/flex/dashboard`
*Daily/Weekly/Monthly device usage summary report based on location*

operationId: `Customer.prototype.getDashboard`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `macs` | query | string | optional | mac list of all devices in the location |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/groups`
*Retrieve customer's groups.*

operationId: `Customer.prototype.getGroups`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/devices/{mac}/resniff`
*Re-enables deviceType sniffing for a particular device.*

<div><strong>204</strong>: Success, your new info looks good.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id, does not exist.</div>
<div><strong>404</strong>: No device found with provided mac address</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.enableDeviceTypeSniffing`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/tos`
*Describes the current state of TOS for the given client.*

<div><strong>200</strong>: Ok.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>404</strong>: No device found with provided mac address</div>
<div><strong>422</strong>: Invalid MAC.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getTos`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/devices/{mac}/tos/reset`
*Resets the back-off and thresholds for the given client.*

<div><strong>200</strong>: Ok.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>404</strong>: No device found with provided mac address</div>
<div><strong>422</strong>: Invalid MAC.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.resetTos`

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mac` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/config/powerManagement`
*Patch Power Management config for the location*

<div><strong>200</strong>: Ok.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: This location is not Power Management capable.</div>
<div><strong>429</strong>: Too many requests.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchPowerManagementConfig`

**Required to call:** `id` (path), `locationId` (path), `mode` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mode` | formData | string | **REQUIRED** | Any of "AUTO", "ENABLE", "DISABLE" |

**Possible responses:** `202` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/event/forcePowerManagement`
*Post Force Power Management event for the location*

<div><strong>200</strong>: Ok.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>422</strong>: This location is not Power Management capable.</div>
<div><strong>422</strong>: Duration must be equal or larger than 0.</div>
<div><strong>422</strong>: This location does not have Power Management enabled.</div>
<div><strong>429</strong>: Too many requests.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.postForcePowerManagementEvent`

**Required to call:** `id` (path), `locationId` (path), `duration` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `duration` | formData | number | **REQUIRED** | value equal or larger than 0 |

**Possible responses:** `202` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/mapConfig`
*Get MAP-E/MAP-T config for the location.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>422</strong>: Multiple validation errors.</div>
<div><strong>429</strong>: Too many requests.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getMapConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/mapConfig`
*Update MAP-E/MAP-T config for the location.*

<div><strong>You must supply at least one of these optional parameter combinations:</strong></div>
<div>{mapRulesDhcp} || {mapRulesUrl} || {bmrIpv6Prefix, bmrIpv4Prefix, bmrEaLength, bmrPsidOffset, dmr}</div>
<div><strong>202</strong>: Success.</div>
<div><strong>401</strong>: Authorization required.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>422</strong>: Multiple validation errors.</div>
<div><strong>429</strong>: Too many requests.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putMapConfig`

**Required to call:** `id` (path), `locationId` (path), `mode` (formData), `mapType` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mode` | formData | string | **REQUIRED** | Any of "AUTO", "ENABLE", "DISABLE" |
| `mapType` | formData | string | **REQUIRED** | Mechanism for Mapping of Address and Port. Any of "MAP_TYPE_E", "MAP_TYPE_T" |
| `mapRulesDhcp` | formData | boolean | optional | Provision MAP rules via DHCPv6 |
| `mapRulesUrl` | formData | string | optional | Provision MAP rules from “v6plus” distribution server |
| `mapLegacyDraft` | formData | boolean | optional | Use MAP legacy RFC draft 03 to calculate MAP IPv6 address |
| `bmrIpv6Prefix` | formData | string | optional | Basic Mapping Rule IPv6 prefix |
| `bmrIpv4Prefix` | formData | string | optional | Basic Mapping Rule IPv4 prefix |
| `bmrEaLength` | formData | number | optional | Basic Mapping Rule EA-bits length |
| `bmrPsidOffset` | formData | number | optional | Basic Mapping Rule PSID offset |
| `dmr` | formData | string | optional | Default Mapping Rule |
| `otherConfig` | formData | string | optional | Array of objects for additional configuration. Provide in format of [{ key: "something1", value: "something2" }] |
| `disableDhcp` | formData | boolean | optional | Disable DHCP Client on WAN side |

**Possible responses:** `202` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/mapConfig`
*Delete the MAP-E/MAP-T config for the location. Does not change the mode.*

<div><strong>202</strong>: Success.</div>
<div><strong>401</strong>: Authorization required.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>422</strong>: Multiple validation errors.</div>
<div><strong>429</strong>: Too many requests.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteMapConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `202` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/mapConfig`
*Update some of the MAP-E/MAP-T config for the location.*

<div><strong>202</strong>: Success.</div>
<div><strong>401</strong>: Authorization required.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>422</strong>: Multiple validation errors.</div>
<div><strong>429</strong>: Too many requests.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchMapConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `mode` | formData | string | optional | Any of "AUTO", "ENABLE", "DISABLE" |
| `otherConfig` | formData | string | optional | Array of objects for additional configuration. Provide in format of [{ key: "something1", value: "something2" }] |

**Possible responses:** `202` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/customerSupportConfigurations`
*Returns partner customer support configuration.*

<div><strong>200</strong>: Success.</div>
<div><strong>404</strong>: customer id or location id does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getCustomerSupportConfigurations`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/taskStatuses`
*Retrieve all task statuses of nodes from controller*

<div><strong>204</strong>: Success.</div>
<div><strong>404</strong>: customer id or location id does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getTaskStatuses`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/securityPolicy/contentFilterCategories`
*Get Content filter categories*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getContentFilterCategories__get_Customers_{id}_securityPolicy_contentFilterCategories`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/securityPolicy/contentFilterCategories/{contentFilter}`
*Get Content filter categories*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getContentFilterCategories__get_Customers_{id}_securityPolicy_contentFilterCategories_{contentFilter}`

**Required to call:** `id` (path), `contentFilter` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `contentFilter` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/contentCategories`
*Get Content categories*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getContentCategories__get_Customers_{id}_contentCategories`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `keyword` | query | string | optional | Name to search |
| `limit` | query | integer | optional | Page limit |
| `offset` | query | integer | optional | Page offset |
| `categoryIds` | query | string | optional | list to categoryIds |
| `lang` | query | string | optional | Language code |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/appTime/contentCategories`
*Get Content categories*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getContentCategories__get_Customers_{id}_appTime_contentCategories`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `keyword` | query | string | optional | Name to search |
| `limit` | query | integer | optional | Page limit |
| `offset` | query | integer | optional | Page offset |
| `categoryIds` | query | string | optional | list to categoryIds |
| `lang` | query | string | optional | Language code |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/persons/{personId}/securityPolicy/customContentFilter`
*Get Person security policy for customContentFilter.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getPersonSecurityPolicyCustomContentFilter`

**Required to call:** `id` (path), `locationId` (path), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `personId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/persons/{personId}/securityPolicy/customContentFilter`
*Delete person level custom content filter.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or group id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deletePersonSecurityPolicyCustomerContentFilter`

**Required to call:** `id` (path), `locationId` (path), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/persons/{personId}/securityPolicy/customContentFilter/blocklist`
*Block categoryIds for person*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putPersonSecurityPolicyCustomerContentFilterBlocklist`

**Required to call:** `id` (path), `locationId` (path), `personId` (path), `categoryIds` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `personId` | path | string | **REQUIRED** |  |
| `categoryIds` | formData | string | **REQUIRED** | CategoryIds to block |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/persons/{personId}/securityPolicy/customContentFilter/allowlist`
*Allow categoryIds for person*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putPersonSecurityPolicyCustomerContentFilterAllowlist`

**Required to call:** `id` (path), `locationId` (path), `personId` (path), `categoryIds` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `personId` | path | string | **REQUIRED** |  |
| `categoryIds` | formData | string | **REQUIRED** | CategoryIds to block |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/persons/{personId}/securityPolicy/safesearch`
*Enable, disable Person level safe search config*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getSafeSearchConfig`

**Required to call:** `id` (path), `locationId` (path), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |
| `networkId` | query | string | optional | Secondary network ID to target |
| `vapType` | query | string | optional | fronthaul (employee) or captivePortal (guest) |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/persons/{personId}/securityPolicy/safesearch`
*Enable, disable Person level safe search config*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteSafeSearchConfig`

**Required to call:** `id` (path), `locationId` (path), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `personId` | path | string | **REQUIRED** |  |
| `networkId` | formData | string | optional | Secondary network ID to target |
| `vapType` | formData | string | optional | fronthaul (employee) or captivePortal (guest) |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/persons/{personId}/securityPolicy/safesearch`
*Enable, disable Person level safe search config*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchSafeSearchConfig`

**Required to call:** `id` (path), `locationId` (path), `safeSearchMode` (formData), `personId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `safeSearchMode` | formData | string | **REQUIRED** | safe search mode: enable, disable, auto (enable by default) |
| `personId` | path | string | **REQUIRED** |  |
| `networkId` | formData | string | optional | Secondary network ID to target |
| `vapType` | formData | string | optional | fronthaul (employee) or captivePortal (guest) |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/qos/prioritization`
*Get network priority config*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getNetworkPrioritizationConfig`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/qos/prioritization`
*Update network prioritization config*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.putNetworkPrioritizationConfig`

**Required to call:** `id` (path), `locationId` (path), `requestBody` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `requestBody` | body | object | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Customers/{id}/locations/{locationId}/qos/prioritization/autoExpire`
*Delete all auto expire network prioritization configs*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.deleteNetworkPrioritizationConfigAutoexpire`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `POST` `/Customers/{id}/locations/{locationId}/qos/prioritization/ftuxEngaged`
*Update Network Priority Ftux Engaged with current timestamp*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.updateNetworkPriorityFtuxEngaged`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/staticData`
*Updates static data of a node*

<div><strong>200</strong>: Success.</div>
<div><strong>204</strong>: Nothing to update.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>404</strong>: Node does not exist.</div>
<div><strong>422</strong>: Input validation failed.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.patchNodeStaticData`

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `nodeId` | path | string | **REQUIRED** |  |
| `radioMac24` | formData | string | optional |  |
| `radioMac50L` | formData | string | optional |  |
| `radioMac50U` | formData | string | optional |  |
| `radioMac50` | formData | string | optional |  |
| `radioMac60` | formData | string | optional |  |
| `ethernetMac` | formData | string | optional |  |
| `ethernet1Mac` | formData | string | optional |  |
| `ultraWideband` | formData | string | optional |  |
| `bluetoothMac` | formData | string | optional |  |
| `thread` | formData | string | optional |  |
| `hasUniqueCertificate` | formData | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/Customers/{id}/locations/{locationId}/devices/{deviceId}/clientReportedDeviceType`
*Create or update client reported device type.*

Updates or creates clientReportedDeviceType on Device model and produces a Kafka message.

operationId: `Customer.prototype.putClientReportedDeviceType`

**Required to call:** `id` (path), `locationId` (path), `deviceId` (path), `name` (formData), `brand` (formData), `model` (formData), `operatingSystem` (formData), `operatingSystemVersion` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `deviceId` | path | string | **REQUIRED** | Device ID |
| `lanIpv4` | formData | string | optional | IPv4 |
| `lanIpv6` | formData | string | optional | IPv6 |
| `name` | formData | string | **REQUIRED** | Device name |
| `brand` | formData | string | **REQUIRED** | Device brand |
| `model` | formData | string | **REQUIRED** | Device model |
| `operatingSystem` | formData | string | **REQUIRED** | Device OS |
| `operatingSystemVersion` | formData | string | **REQUIRED** | Device OS version |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Not Found; `422` Invalid request; `500` Unhandled API error

#### `GET` `/Customers/{id}/locations/{locationId}/getWagTunnelStatus`
*Get WAG tunnel status.*

Gets WAG tunnel status.

operationId: `Customer.prototype.getWagTunnelStatus`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Location not found; `500` Unhandled API error

#### `GET` `/Customers/{id}/locations/{locationId}/getDynamicCohortIds`
*Get dynamic cohort ids.*

Get dynamic cohort ids.

operationId: `Customer.prototype.getDynamicCohortIds`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Location not found; `500` Unhandled API error

#### `PATCH` `/Customers/{id}/locations/{locationId}/config/resendTopology`
*Resend topology.*

Resend topology with set intervals for a specified location.

Used for debugging purposes.

operationId: `Customer.prototype.resendTopology`

**Required to call:** `id` (path), `locationId` (path), `monitorIntervalMs` (formData), `publishIntervalMs` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `monitorIntervalMs` | formData | number | **REQUIRED** |  |
| `publishIntervalMs` | formData | number | **REQUIRED** |  |

**Possible responses:** `202` Request was successful; `401` Authorization failed; `404` Customer or location not found; `422` Invalid request; `500` Unhandled API error

#### `GET` `/Customers/{id}/auth-logs`
*Retrieve customer auth logs from IDP*

Retrieves the customer authentication logs.

Logs are retrieved via calling GlobalAuth service.

operationId: `Customer.prototype.getAuthLogs`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Customer not found; `500` Unhandled API error

#### `GET` `/Customers/{id}/locations/{locationId}/secure-identifier`
*Get AES-encrypted identifier for mobile app*

Returns an AES-encrypted identifier combining customerId and locationId.

operationId: `Customer.prototype.getSecureIdentifier`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` There are no locations with the ID "875e0fc9f17ab7add6dce46e"; `500` Unhandled API error

#### `GET` `/Customers/{id}/locations/{locationId}/dhcpLeases`
*Returns DHCP leases from Controller*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: LocationId not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDhcpLeasesFromController`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/dpp/announcements`
*Returns DPP announcements from controller*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getDppAnnouncementsFromController`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/kvStates`
*Retrieve all kvStates on a particular Node for a Location ID.*

<div><strong>200</strong>: Success, your new info looks good.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist.</div>
<div><strong>422</strong>: nodeId must be defined.</div>
<div><strong>425</strong>: nodeId must belong to the location.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getLocationKvStates`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/vlanServices`
*Returns vlanServices from Customer location state*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or WifiNetwork does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.vlanServices`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/firmware/modules`
*Retrieve all firmaware modules for a Location ID.*

<div><strong>200</strong>: Success, your new info looks good.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getFirmwareModules`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/securityPolicy/realizedState`
*Retrieve all securityStates for a Location ID.*

<div><strong>200</strong>: Success, your new info looks good.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Customer.prototype.getSecurityRealizedStates`

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |

**Possible responses:** `200` Request was successful

### Location
Plume internal-only APIs.

#### `GET` `/Locations/{id}/invitations/{fk}`
*Find a related item by id for invitations.*

operationId: `Location.prototype.__findById__invitations`

**Required to call:** `id` (path), `fk` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `fk` | path | string | **REQUIRED** | Foreign key for invitations |

**Possible responses:** `200` Request was successful

#### `PUT` `/Locations/{id}/invitations/{fk}`
*Update a related item by id for invitations.*

operationId: `Location.prototype.__updateById__invitations`

**Required to call:** `id` (path), `fk` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `fk` | path | string | **REQUIRED** | Foreign key for invitations |
| `data` | body | Invitation | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Locations/{id}/invitations/{fk}`
*Delete a related item by id for invitations.*

operationId: `Location.prototype.__destroyById__invitations`

**Required to call:** `id` (path), `fk` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `fk` | path | string | **REQUIRED** | Foreign key for invitations |

**Possible responses:** `204` Request was successful

#### `GET` `/Locations/{id}/_pendingWhitelistRequests/{fk}`
*Find a related item by id for _pendingWhitelistRequests.*

operationId: `Location.prototype.__findById___pendingWhitelistRequests`

**Required to call:** `id` (path), `fk` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `fk` | path | string | **REQUIRED** | Foreign key for _pendingWhitelistRequests |

**Possible responses:** `200` Request was successful

#### `PUT` `/Locations/{id}/_pendingWhitelistRequests/{fk}`
*Update a related item by id for _pendingWhitelistRequests.*

operationId: `Location.prototype.__updateById___pendingWhitelistRequests`

**Required to call:** `id` (path), `fk` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `fk` | path | string | **REQUIRED** | Foreign key for _pendingWhitelistRequests |
| `data` | body | PendingWhitelistRequests | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Locations/{id}/_pendingWhitelistRequests/{fk}`
*Delete a related item by id for _pendingWhitelistRequests.*

operationId: `Location.prototype.__destroyById___pendingWhitelistRequests`

**Required to call:** `id` (path), `fk` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `fk` | path | string | **REQUIRED** | Foreign key for _pendingWhitelistRequests |

**Possible responses:** `204` Request was successful

#### `GET` `/Locations/{id}/_goals/{fk}`
*Find a related item by id for _goals.*

operationId: `Location.prototype.__findById___goals`

**Required to call:** `id` (path), `fk` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `fk` | path | string | **REQUIRED** | Foreign key for _goals |

**Possible responses:** `200` Request was successful

#### `PUT` `/Locations/{id}/_goals/{fk}`
*Update a related item by id for _goals.*

operationId: `Location.prototype.__updateById___goals`

**Required to call:** `id` (path), `fk` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `fk` | path | string | **REQUIRED** | Foreign key for _goals |
| `data` | body | Goal | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Locations/{id}/_goals/{fk}`
*Delete a related item by id for _goals.*

operationId: `Location.prototype.__destroyById___goals`

**Required to call:** `id` (path), `fk` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `fk` | path | string | **REQUIRED** | Foreign key for _goals |

**Possible responses:** `204` Request was successful

#### `GET` `/Locations/{id}/_nodePlacementSessions/{fk}`
*Find a related item by id for _nodePlacementSessions.*

operationId: `Location.prototype.__findById___nodePlacementSessions`

**Required to call:** `id` (path), `fk` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `fk` | path | string | **REQUIRED** | Foreign key for _nodePlacementSessions |

**Possible responses:** `200` Request was successful

#### `PUT` `/Locations/{id}/_nodePlacementSessions/{fk}`
*Update a related item by id for _nodePlacementSessions.*

operationId: `Location.prototype.__updateById___nodePlacementSessions`

**Required to call:** `id` (path), `fk` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `fk` | path | string | **REQUIRED** | Foreign key for _nodePlacementSessions |
| `data` | body | PlacementSession | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Locations/{id}/_nodePlacementSessions/{fk}`
*Delete a related item by id for _nodePlacementSessions.*

operationId: `Location.prototype.__destroyById___nodePlacementSessions`

**Required to call:** `id` (path), `fk` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `fk` | path | string | **REQUIRED** | Foreign key for _nodePlacementSessions |

**Possible responses:** `204` Request was successful

#### `GET` `/Locations/{id}/nodes`
*Queries nodes of Location.*

operationId: `Location.prototype.__get__nodes`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `filter` | query | string | optional |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Locations/{id}/nodes`
*Claim all nodes for a Location ID.*

<div><strong>204</strong>: Success.</div>
<div><strong>400</strong>: Required nodes field is missing.</div>
<div><strong>422</strong>: Request contain wrong value or exceded the max number of 32 pods to claim.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.claimMultipleNodes`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `nodes` | formData | string | optional | array of serialNumber/ids |

**Possible responses:** `200` Request was successful

#### `GET` `/Locations/{id}/invitations`
*Queries invitations of Location.*

operationId: `Location.prototype.__get__invitations`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `filter` | query | string | optional |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Locations/{id}/invitations`
*Creates a new instance in invitations of this model.*

operationId: `Location.prototype.__create__invitations`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `data` | body | Invitation | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Locations/{id}/invitations`
*Deletes all invitations of this model.*

operationId: `Location.prototype.__delete__invitations`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |

**Possible responses:** `204` Request was successful

#### `GET` `/Locations/{id}/invitations/count`
*Counts invitations of Location.*

operationId: `Location.prototype.__count__invitations`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `where` | query | string | optional | Criteria to match model instances |

**Possible responses:** `200` Request was successful

#### `GET` `/Locations/{id}/_pendingWhitelistRequests`
*Queries _pendingWhitelistRequests of Location.*

operationId: `Location.prototype.__get___pendingWhitelistRequests`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `filter` | query | string | optional |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Locations/{id}/_pendingWhitelistRequests`
*Creates a new instance in _pendingWhitelistRequests of this model.*

operationId: `Location.prototype.__create___pendingWhitelistRequests`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `data` | body | PendingWhitelistRequests | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Locations/{id}/_pendingWhitelistRequests`
*Deletes all _pendingWhitelistRequests of this model.*

operationId: `Location.prototype.__delete___pendingWhitelistRequests`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |

**Possible responses:** `204` Request was successful

#### `GET` `/Locations/{id}/_pendingWhitelistRequests/count`
*Counts _pendingWhitelistRequests of Location.*

operationId: `Location.prototype.__count___pendingWhitelistRequests`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `where` | query | string | optional | Criteria to match model instances |

**Possible responses:** `200` Request was successful

#### `GET` `/Locations/{id}/_goals`
*Queries _goals of Location.*

operationId: `Location.prototype.__get___goals`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `filter` | query | string | optional |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Locations/{id}/_goals`
*Creates a new instance in _goals of this model.*

operationId: `Location.prototype.__create___goals`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `data` | body | Goal | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Locations/{id}/_goals`
*Deletes all _goals of this model.*

operationId: `Location.prototype.__delete___goals`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |

**Possible responses:** `204` Request was successful

#### `GET` `/Locations/{id}/_goals/count`
*Counts _goals of Location.*

operationId: `Location.prototype.__count___goals`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `where` | query | string | optional | Criteria to match model instances |

**Possible responses:** `200` Request was successful

#### `GET` `/Locations/{id}/_nodePlacementSessions`
*Queries _nodePlacementSessions of Location.*

operationId: `Location.prototype.__get___nodePlacementSessions`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `filter` | query | string | optional |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Locations/{id}/_nodePlacementSessions`
*Creates a new instance in _nodePlacementSessions of this model.*

operationId: `Location.prototype.__create___nodePlacementSessions`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `data` | body | PlacementSession | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Locations/{id}/_nodePlacementSessions`
*Deletes all _nodePlacementSessions of this model.*

operationId: `Location.prototype.__delete___nodePlacementSessions`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |

**Possible responses:** `204` Request was successful

#### `GET` `/Locations/{id}/_nodePlacementSessions/count`
*Counts _nodePlacementSessions of Location.*

operationId: `Location.prototype.__count___nodePlacementSessions`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `where` | query | string | optional | Criteria to match model instances |

**Possible responses:** `200` Request was successful

#### `GET` `/Locations/{id}`
*Find a model instance by {{id}} from the data source.*

operationId: `Location.findById`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Model id |
| `filter` | query | string | optional | Filter defining fields and include - must be a JSON-encoded string ({"something":"value"}) |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Locations/{id}`
*Update uprise value for the location*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.patchUpriseOrFlex`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `uprise` | formData | boolean | optional |  |
| `flex` | formData | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Locations`
*Find all instances of the model matched by filter from the data source.*

operationId: `Location.find`

**Required to call:** none

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `filter` | query | string | optional | Filter defining fields, where, include, order, offset, and limit - must be a JSON-encoded string (`{"where":{"something":"value"}}`).  See https://loopback.io/doc/en/lb3/Querying-data.html#using-stringified-json-in-rest-queries for more details. |

**Possible responses:** `200` Request was successful

#### `GET` `/Locations/count`
*Count instances of the model matched by where from the data source.*

operationId: `Location.count`

**Required to call:** none

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `where` | query | string | optional | Criteria to match model instances |

**Possible responses:** `200` Request was successful

#### `GET` `/Locations/{id}/backhaul`
*Retrieve location's backhaul configuration.*

operationId: `Location.prototype.getBackhaul`

**Required to call:** `id` (path), `locationId` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `locationId` | query | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Locations/{id}/secondaryNetworks/captivePortals/{networkId}/gdprRetrieve`
*Get guest captive portal gdpr data.*

Gets guest captive portal gdpr data.


operationId: `Location.prototype.getNewGuestCaptivePortalGdprData`

**Required to call:** `id` (path), `networkId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `networkId` | path | string | **REQUIRED** | Network ID |
| `page` | query | number | optional |  |
| `limit` | query | number | optional |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Location, or network not found; `500` Unhandled API error

#### `GET` `/Locations/{id}/forceGraph`
*Vertices[] and edges[] used to display a Network Topology.*

<div>The data used to initialize and dynamically display and update a Topology.</div>
<div>Can also be used to get a network's list of nodes + devices (a.k.a. vertices) and links (a.k.a., edges).</div><div>&nbsp;</div>
<div><strong>200</strong>: Success, graph structure returned.</div>
<div><strong>404</strong>: customer id or location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.getForceGraph`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `allSSIDs` | query | boolean | optional |  |
| `showPartnerComponent` | query | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Locations/{id}/gatewayAccount`
*Get AccountID and GatwewayID of a location*

<div><strong>200</strong>: Success, accountID and gatewayID returned.</div>
<div><strong>404</strong>: Location does not exist</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.getGatewayAccount`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |

**Possible responses:** `200` Request was successful

#### `GET` `/Locations/{id}/devices/{mac}`
*Get the name and icon of device by mac lookup*

<div>To be used by notification for fetching device name and icon.</div>
<div><strong>200</strong>: Success, device details returned.</div>
<div><strong>404</strong>: Location ID or Device mac not found</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.getDevicesByMacName`

**Required to call:** `id` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `mac` | path | string | **REQUIRED** | mac of device |

**Possible responses:** `200` Request was successful

#### `GET` `/Locations/{id}/devices/{mac}/detailsWithSsid`
*Get device parameters by mac id and the ssid by networkId*

<div>To be used by notification for fetching device name and icon.</div>
<div><strong>200</strong>: Success, device details returned.</div>
<div><strong>404</strong>: Location ID, Device mac or Network id not found</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.deviceDetailsWithSsid`

**Required to call:** `id` (path), `mac` (path), `networkId` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `mac` | path | string | **REQUIRED** | mac of device |
| `networkId` | query | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Locations/{id}/rooms/search/{search}`
*Internal integration use only: Search to identify if the node or device is assigned to a room.*

<div>To be used by Notification API for fetching Room info.</div>
<div><strong>200</strong>: Success, room details returned.</div>
<div><strong>404</strong>: Location, device or node not found</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.findRoomByNodeIdNodeMacAndDeviceMac`

**Required to call:** `id` (path), `search` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `search` | path | string | **REQUIRED** | Node ID (Serial Number), Node WiFi Radio Mac, or Device Mac |

**Possible responses:** `200` Request was successful

#### `GET` `/Locations/{id}/homeAway`
*Get the homeAway configs to use for a location*

<div><strong>200</strong>: Success, accountID and gatewayID returned.</div>
<div><strong>404</strong>: Location does not exist</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.getHomeAwayConfig`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |

**Possible responses:** `200` Request was successful

#### `GET` `/Locations/{id}/appTime`
*Get the appTime configs to use for a location*

<div><strong>200</strong>: Success, accountID and gatewayID returned.</div>
<div><strong>404</strong>: Location does not exist</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.getAppTime`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |

**Possible responses:** `200` Request was successful

#### `POST` `/Locations/{id}/devices/{mac}/securityPolicy/anomaly/websites/blacklist`
*Update a Device's Anomaly Security Policy for a location ID to include a blacklisted website.*

<div><strong>200</strong>: Success.</div>
<div><strong>400</strong>: Required fields missing or field type is incorrect.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, or Device does not exist and is not known to Plume</div>
<div><strong>422</strong>: DNS value is invalid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.postDeviceSecurityPolicyAnomalyBlacklist`

**Required to call:** `id` (path), `mac` (path), `deviceType` (formData), `fqdn` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `mac` | path | string | **REQUIRED** |  |
| `deviceType` | formData | string | **REQUIRED** |  |
| `fqdn` | formData | string | **REQUIRED** |  |
| `ipv4` | formData | string | optional |  |
| `ipv6` | formData | string | optional |  |
| `ttl` | formData | number | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Locations/{id}/devices/{mac}/securityPolicy/anomaly/websites/blacklist/{fqdn}`
*Update a Location's Anomaly Security Policy for a location ID to remove a blacklisted DNS entry.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, WifiNetwork, Device or DNS does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.deleteDeviceSecurityPolicyAnomalyBlacklist`

**Required to call:** `id` (path), `mac` (path), `fqdn` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `mac` | path | string | **REQUIRED** |  |
| `fqdn` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `GET` `/Locations/{id}/homeSecurity`
*Fetch the home security configuration for this location*

<div><strong>200</strong>: Success, HomeSecurity object returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.getHomeSecurity`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Locations/{id}/homeSecurity`
*Enable/disable live motion streaming and/or motion events for this location*

<div><strong>200</strong>: Success, updated HomeSecurity object returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.patchHomeSecurity`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `source` | formData | string | optional | Source of patch request; must be one of "user" or "geofence" |
| `liveMotionEnabled` | formData | boolean | optional |  |
| `motionEventsEnabled` | formData | boolean | optional |  |
| `homeAwayActive` | formData | boolean | optional | Enable/disable motion events based on location Homeaway state |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Locations/{id}/homeSecurity/sensitivity`
*Configure motion event configuration for this location*

<div><strong>200</strong>: Success, updated HomeSecurity object returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.patchHomeSecuritySensitivity`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `cooldown` | formData | number | optional | sets required rest period for motion detected events to end, in seconds |
| `petMode` | formData | string | optional | adjusts sensitivity of motion detected events for pets; must be one of "none", "under10", "10to30", "over30" and can only be set if sensitivity = high |
| `sensitivity` | formData | string | optional | adjusts sensitivity of motion detected events; must be one of "low", "medium", "high" |

**Possible responses:** `200` Request was successful

#### `GET` `/Locations/{id}/homeSecurity/motionHistory`
*Fetch the motion density history for this location*

<div><strong>200</strong>: Success, motion density array returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.getMotionHistory`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `from` | query | number | optional | UTC unix ts |
| `to` | query | number | optional | UTC unix ts, defaults to now |
| `bucket` | query | number | optional | number of seconds in density calculation window; returned data points represent % of non-zero intensity values in the window |

**Possible responses:** `200` Request was successful

#### `GET` `/Locations/{id}/homeSecurity/motionHistory/state`
*Fetch the motion state history for this location*

<div><strong>200</strong>: Success, motion state array returned (Each element of the array is in the form ["val", "unix_ts"], where "val" is one of: 
<div>0 - Not armed, not tripped</div>
<div>1 - Not armed, tripped</div>
<div>2 - Armed, not tripped</div>
<div>3 - Armed, tripped</div></div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.getMotionStateHistory`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `from` | query | number | optional | UTC unix ts |
| `to` | query | number | optional | UTC unix ts, defaults to now |
| `bucket` | query | number | optional | number of seconds in density calculation window; returned data points represent % of non-zero intensity values in the window |

**Possible responses:** `200` Request was successful

#### `GET` `/Locations/{id}/homeSecurity/events/history`
*Fetch the event history for this location*

<div><strong>200</strong>: Success, event array returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.getEventHistory`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `from` | query | number | optional | UTC unix ts |
| `to` | query | number | optional | UTC unix ts, defaults to now |
| `category` | query | string | optional | Filter events by category (Motion or Plume [config changes]). Multiple categories can be passed as a comma-separated string. Default is both. |
| `limit` | query | number | optional | Maximum number of events to return; defaults to 10 |
| `sort` | query | boolean | optional | whether the returned events will be post-sorted by timestamp |

**Possible responses:** `200` Request was successful

#### `GET` `/Locations/{id}/homeSecurity/devices/sounding`
*Fetch the sounding states for eligible devices in this location*

<div><strong>200</strong>: Success, device sounding states returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.getDeviceSoundingState`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `mac` | query | string | optional | Optional mac address for single device lookup (fetches all devices by default) |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Locations/{id}/homeSecurity/devices/sounding`
*Patch the sounding states for the given devices*

<div><strong>200</strong>: Success, device sounding states returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.patchDeviceSoundingState`

**Required to call:** `id` (path), `soundingStates` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `soundingStates` | body | object | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/Locations/{id}/councilman/resync`
*Push Security Configurations to Councilman.*

<div><strong>204</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.putCouncilmanResync`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |

**Possible responses:** `204` Request was successful

#### `GET` `/Locations/{id}/wifiMotion`
*Get WifiMotion config for this location*

<div><strong>200</strong>: Success, wifiMotion object returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.getWifiMotion`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Locations/{id}/wifiMotion`
*Enable/disable WifiMotion feature for this location*

<div><strong>200</strong>: Success, updated object returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.patchWifiMotion`

**Required to call:** `id` (path), `auto` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `auto` | formData | boolean | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Locations/{id}/nasRedirect`
*Handle proxy redirects from walled-garden networks requesting network access*

<div><strong>200</strong>: Success, redirect URL returned.</div>
<div><strong>404</strong>: Location does not exist</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.nasRedirect`

**Required to call:** `id` (path), `proxy` (query), `proxyMac` (query), `nodeMac` (query), `ssid` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `proxy` | query | string | **REQUIRED** | client IP address |
| `proxyMac` | query | string | **REQUIRED** | client MAC address |
| `nodeMac` | query | string | **REQUIRED** | gateway MAC address |
| `ssid` | query | string | **REQUIRED** | guest SSID client is attempting to join |

**Possible responses:** `200` Request was successful

#### `GET` `/Locations/{id}/summary`
*Get the locationSummary for this location*

<div><strong>200</strong>: Success, wifiMotion object returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.getLocationSummary`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |

**Possible responses:** `200` Request was successful

#### `PUT` `/Locations/{id}/resyncLocation`
*Trigger Controller to refresh all Customer mongo data for a Location ID.*

<div><strong>200</strong>: Success, triggered right way.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.putResyncLocation`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Locations/{id}/nodes/{nodeId}`
*Unclaim a particular Node from a Location with the option of preserving the original Package ID.*

<div><strong>204</strong>: Success, a job well done.</div>
<div><strong>400</strong>: Pod already unclaimed.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>403</strong>: the node is online, and can not be unclaimed.<br/>
<div><strong>404</strong>: location id not found, nodeId missing from URL,<br/> or location has zero owned pods.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.unclaimNode`

**Required to call:** `id` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `nodeId` | path | string | **REQUIRED** |  |
| `preservePackId` | formData | boolean | optional | Whether or not packId should remain the same |
| `forceUnclaim` | formData | boolean | optional | Unclaim regardless of pod connectivity |
| `purgeGroupIds` | formData | boolean | optional | Whether or not groupIds should be kept on the node |
| `removeAccountId` | formData | boolean | optional | delete account id on the inventory node |
| `unclaimReason` | formData | string | optional | Used by controller to determine what actions to take for nodeClaimChanged |
| `incrementFactoryResetCounter` | formData | boolean | optional | Whether or not to increment the factory reset counter |

**Possible responses:** `204` Request was successful

#### `GET` `/Locations/{id}/marketingExport`
*Get detailed information of location for updating CRMs.*

<div><strong>200</strong>: Success, location data in response.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.marketingExport`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Locations/{id}/networkAccess/networks/{networkId}`
*Patch the network access network object's captivePortal field.*

<div><strong>204</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist.</div>
<div><strong>404</strong>: Network does not exist.</div>

operationId: `Location.prototype.patchNetworkAccessNetworkCaptivePortalEnabled`

**Required to call:** `id` (path), `networkId` (path), `requestBody` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `networkId` | path | string | **REQUIRED** | Network ID |
| `requestBody` | body | object | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `GET` `/Locations/{id}/partnerIdProfileInfo`
*Get the partner id, location profile and other info for this location*

<div><strong>200</strong>: Success, wifiMotion object returned.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: location id does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.getLocationPartnerIdProfileInfo`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |

**Possible responses:** `200` Request was successful

#### `GET` `/Locations/{id}/groupProvisioning`
*Get Group Provisioning details*

<div><strong>200</strong>: Success.</div>
<div><strong>404</strong>: Location does not exist</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.groupProvisioning`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |

**Possible responses:** `200` Request was successful

#### `POST` `/Locations/{id}/resyncWebconfig`
*sync SSID data from location to all its claimed nodes.*

<div><strong>204</strong>: Success.</div>
<div><strong>404</strong>: Wifi network does not exist.</div>
<div><strong>404</strong>: location id, does not exist.</div>
<div><strong>422</strong>: Endpoint is not allowed in current deployment.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.resyncWebconfig`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |

**Possible responses:** `200` Request was successful

#### `POST` `/Locations/{id}/secondaryNetworks/fronthauls/iot/propagate`
*Propagates an IOT Front Haul Network to this Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or NetworkId does not exist and is not known to Plume</div>
<div><strong>409</strong>: This location already has a fronthaul with ssid</div>
<div><strong>422</strong>: NetworkId/SSIDs must be the unique and valid values.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.propagateIotFrontHaul`

**Required to call:** `id` (path), `originIotNetworkLocationId` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `originIotNetworkLocationId` | formData | string | **REQUIRED** |  |
| `isPublic` | formData | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `POST` `/Locations/validateSsidUniqueness`
*Validates the uniqueness of an SSID across locations.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>422</strong>: NetworkId/SSIDs must be the unique and valid values.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.validateSsidUniqueness`

**Required to call:** `ssid` (formData), `locationIds` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `ssid` | formData | string | **REQUIRED** |  |
| `locationIds` | formData | string | **REQUIRED** |  |
| `options` | formData | string | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Locations/{id}/secondaryNetworks/fronthauls/iot`
*Gets an IOT Front Haul Network for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id/NetworkId does not exist and is not known to Plume</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.getIotFrontHaul`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |

**Possible responses:** `200` Request was successful

#### `POST` `/Locations/{id}/secondaryNetworks/fronthauls/iot`
*Create an IOT Front Haul Network for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or NetworkId does not exist and is not known to Plume</div>
<div><strong>422</strong>: NetworkId/SSIDs must be the unique and valid values.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.postIotFrontHaul`

**Required to call:** `id` (path), `propertyId` (formData), `ssid` (formData), `encryptionKey` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `propertyId` | formData | string | **REQUIRED** |  |
| `ssid` | formData | string | **REQUIRED** |  |
| `encryptionKey` | formData | string | **REQUIRED** |  |
| `wpaMode` | formData | string | optional |  |
| `securityPolicy` | formData | string | optional |  |
| `radioEnablement` | formData | string | optional |  |
| `ssidBroadcast` | formData | boolean | optional |  |
| `accessZone` | formData | string | optional |  |
| `isPublic` | formData | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Locations/{id}/secondaryNetworks/fronthauls/iot`
*Delete an IOT Front Haul for a Location ID.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id/NetworkId does not exist and is not known to Plume</div>
<div><strong>409</strong>: Location has propagated IOT fronthauls</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.deleteIotFrontHaul`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |

**Possible responses:** `204` Request was successful

#### `PATCH` `/Locations/{id}/secondaryNetworks/fronthauls/iot`
*Update an IOT Front Haul for a given Location ID/NetworkId.*

<div><strong>200</strong>: Success.</div>
<div><strong>401</strong>: Authorization required or customer id not found.</div>
<div><strong>404</strong>: Location id or NetworkId does not exist and is not known to Plume</div>
<div><strong>422</strong>: NetworkId/SSIDs must be the unique and valid values.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Location.prototype.patchIotFrontHaul`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Location id |
| `ssid` | formData | string | optional |  |
| `encryptionKey` | formData | string | optional |  |
| `wpaMode` | formData | string | optional |  |
| `securityPolicy` | formData | string | optional |  |
| `radioEnablement` | formData | string | optional |  |
| `ssidBroadcast` | formData | boolean | optional |  |

**Possible responses:** `200` Request was successful

### Node
internal-only APIs.

#### `GET` `/Nodes/{id}`
*Find a model instance by {{id}} from the data source.*

operationId: `Node.findById`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Model id |
| `filter` | query | string | optional | Filter defining fields and include - must be a JSON-encoded string ({"something":"value"}) |

**Possible responses:** `200` Request was successful

#### `DELETE` `/Nodes/{id}`
*Unclaim a node by a groupAdmin or admin*

<div><strong>204</strong>: Success, node changed.</div>
<div><strong>401</strong>: Authorization required.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Node.prototype.unclaim`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Node id |
| `forceUnclaim` | formData | boolean | optional |  |
| `preservePackId` | formData | boolean | optional |  |

**Possible responses:** `204` Request was successful

#### `GET` `/Nodes`
*Find all instances of the model matched by filter from the data source.*

operationId: `Node.find`

**Required to call:** none

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `filter` | query | string | optional | Filter defining fields, where, include, order, offset, and limit - must be a JSON-encoded string (`{"where":{"something":"value"}}`).  See https://loopback.io/doc/en/lb3/Querying-data.html#using-stringified-json-in-rest-queries for more details. |

**Possible responses:** `200` Request was successful

#### `POST` `/Nodes`
*Import a node into the global/shared inventory (does NOT claim).*

<div><strong>200</strong>: Success, node imported.</div>
<div><strong>401</strong>: Authorization required.</div>
<div><strong>409</strong>: NodeId already exists in shared inventory.</div>
<div><strong>422</strong>: Input validation failed.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Node.customCreate`

**Required to call:** `id` (formData), `residentialGateway` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | formData | string | **REQUIRED** |  |
| `residentialGateway` | formData | boolean | **REQUIRED** |  |
| `model` | formData | string | optional | Node model ID value is required unless a Partner ID exemption has been configured |
| `packId` | formData | string | optional | optional packId to group nodes |
| `partnerId` | formData | string | optional | Partner ID required on Plume production clouds |
| `radioMac24` | formData | string | optional | optional radioMac24, must be a valid mac address |
| `radioMac50` | formData | string | optional | optional radioMac50, must be a valid mac address |
| `radioMac60` | formData | string | optional | optional radioMac60, must be a valid mac address |
| `ethernetMac` | formData | string | optional | optional ethernetMac, must be a valid mac address |
| `ethernet1Mac` | formData | string | optional | optional ethernet1Mac, must be a valid mac address |
| `claimKeyRequired` | formData | boolean | optional | optional claimKeyRequired, default is false |
| `radioMac50L` | formData | string | optional | optional radioMac50L, must be a valid mac address |
| `radioMac50U` | formData | string | optional | optional radioMac50U, must be a valid mac address |
| `subscriptionRequired` | formData | boolean | optional | optional subscriptionRequired, default is false |
| `thread` | formData | string | optional | optional Thread/Matter MAC addres |
| `ultraWideband` | formData | string | optional | optional ultraWideband, must be a valid mac address |
| `bluetoothMac` | formData | string | optional | optional bluetoothMac, must be a valid mac address |

**Possible responses:** `200` Request was successful

#### `GET` `/Nodes/count`
*Count instances of the model matched by where from the data source.*

operationId: `Node.count`

**Required to call:** none

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `where` | query | string | optional | Criteria to match model instances |

**Possible responses:** `200` Request was successful

#### `GET` `/Nodes/{id}/customer`
*Get the customer info with the node Id.*

<div><strong>200</strong>: Success, return the customer info.</div>
<div><strong>403</strong>: Public ip not matched.</div>
<div><strong>404</strong>: NodeId not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Node.prototype.getCustomerByNodeId`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Node id |

**Possible responses:** `200` Request was successful

#### `GET` `/Nodes/{id}/mqtt`
*Get the MQTT broker address of the node.*

<div><strong>200</strong>: Success, return the customer info.</div>
<div><strong>404</strong>: NodeId not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Node.prototype.getMqttBroker`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Node id |

**Possible responses:** `200` Request was successful

#### `POST` `/Nodes/{id}/passwordLessToken`
*Update the name and email for customer and generate emailToken and appToken.*

<div><strong>200</strong>: Success, return the customer info.</div>
<div><strong>403</strong>: Public ip not matched.</div>
<div><strong>404</strong>: NodeId not found.</div>
<div><strong>422</strong>: Email must be defined and valid.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Node.prototype.verifyEmailPasswordlessToken`

**Required to call:** `id` (path), `name` (formData), `email` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Node id |
| `name` | formData | string | **REQUIRED** |  |
| `email` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/Nodes/{id}/packId`
*Rename an unclaimed node/pod's packId in global inventory.*

<div><strong>200</strong>: Success, a job well done.</div>
<div><strong>400</strong>: Bad request, packId is undefined or empty string.</div>
<div><strong>404</strong>: NodeId not found.</div>
<div><strong>422</strong>: PackId is invalid (too long).</div>
<div><strong>423</strong>: PackId cannot be changed for a claimed pod.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Node.updatePackId`

**Required to call:** `id` (path), `packId` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |
| `packId` | formData | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

### Inventory
Inventory APIs

#### `GET` `/inventory/nodes/{nodeId}`
*Get node by ID from the Inventory service*

<div><strong>200</strong>: Success, return the node object</div>
<div><strong>401</strong>: Authorization required.</div>
<div><strong>404</strong>: Node not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Inventory.getNodeById`

**Required to call:** `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `nodeId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `POST` `/inventory/nodes`
*Import a node into the global/shared inventory (does NOT claim).*

<div><strong>200</strong>: Success, node imported.</div>
<div><strong>401</strong>: Authorization required.</div>
<div><strong>409</strong>: NodeId already exists in shared inventory.</div>
<div><strong>422</strong>: Input validation failed.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Inventory.createNode`

**Required to call:** `id` (formData), `residentialGateway` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | formData | string | **REQUIRED** |  |
| `residentialGateway` | formData | boolean | **REQUIRED** |  |
| `model` | formData | string | optional | Node model ID value is required unless a Partner ID exemption has been configured |
| `packId` | formData | string | optional | optional packId to group nodes |
| `partnerId` | formData | string | optional | Partner ID required on Plume production clouds |
| `radioMac24` | formData | string | optional | optional radioMac24, must be a valid mac address |
| `radioMac50` | formData | string | optional | optional radioMac50, must be a valid mac address |
| `radioMac60` | formData | string | optional | optional radioMac60, must be a valid mac address |
| `ethernetMac` | formData | string | optional | optional ethernetMac, must be a valid mac address |
| `ethernet1Mac` | formData | string | optional | optional ethernet1Mac, must be a valid mac address |
| `claimKeyRequired` | formData | boolean | optional | optional claimKeyRequired, default is false |
| `radioMac50L` | formData | string | optional | optional radioMac50L, must be a valid mac address |
| `radioMac50U` | formData | string | optional | optional radioMac50U, must be a valid mac address |
| `subscriptionRequired` | formData | boolean | optional | optional subscriptionRequired, default is false |
| `thread` | formData | string | optional | optional Thread/Matter MAC addres |
| `ultraWideband` | formData | string | optional | optional ultraWideband, must be a valid mac address |
| `bluetoothMac` | formData | string | optional | optional bluetoothMac, must be a valid mac address |

**Possible responses:** `200` Request was successful

#### `PATCH` `/inventory/nodes/{nodeId}/autoProvisioning`
*S node by ID from the Inventory service*

<div><strong>200</strong>: Success, return the node object</div>
<div><strong>401</strong>: Authorization required.</div>
<div><strong>404</strong>: Node not found.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `Inventory.autoProvisioning`

**Required to call:** `nodeId` (path), `autoProvisionToThisDeployment` (formData)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `nodeId` | path | string | **REQUIRED** |  |
| `autoProvisionToThisDeployment` | formData | boolean | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

### IntegrationHealthCheck
Secure health check

#### `GET` `/checkIntegrationHealth`
*Integration Health check API 2.0*

<div><strong>200</strong>: Success, Integration intact.</div>
<div><strong>401</strong>: Authorization required.</div>

operationId: `IntegrationHealthCheck.checkIntegration`

**Parameters:** none

**Possible responses:** `204` Request was successful

### PartnerConfig
Persists all dynamic partner based config managed by customer

#### `GET` `/partnerConfig/{id}/captivePortalTerms`
*Fetches hasOne relation captivePortalTerms.*

operationId: `PartnerConfig.prototype.__get__captivePortalTerms`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | PartnerConfig id |
| `refresh` | query | boolean | optional |  |

**Possible responses:** `200` Request was successful

#### `POST` `/partnerConfig/{id}/captivePortalTerms`
*Creates a new instance in captivePortalTerms of this model.*

operationId: `PartnerConfig.prototype.__create__captivePortalTerms`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | PartnerConfig id |
| `data` | body | PartnerCaptivePortalTerms | optional |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/partnerConfig/{id}/captivePortalTerms`
*Update captivePortalTerms of this model.*

operationId: `PartnerConfig.prototype.__update__captivePortalTerms`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | PartnerConfig id |
| `data` | body | PartnerCaptivePortalTerms | optional |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/partnerConfig/{id}/captivePortalTerms`
*Deletes captivePortalTerms of this model.*

operationId: `PartnerConfig.prototype.__destroy__captivePortalTerms`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | PartnerConfig id |

**Possible responses:** `204` Request was successful

#### `GET` `/partnerConfig/{partnerId}/qos/appPrioritization`
*Get status for app prioritization.*

Get status for app prioritization for a given partner.
Returns the current configuration related to application traffic prioritization.

operationId: `PartnerConfig.getAppPrioritizationPartnerConfig`

**Required to call:** `partnerId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `partnerId` | path | string | **REQUIRED** | partner Id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Partner id or WifiNetwork does not exist and is not known to Plume; `500` Unhandled API error

#### `PATCH` `/partnerConfig/{partnerId}/qos/appPrioritization`
*Update app prioritization config.*

Update the app prioritization configuration for a given partner.
Allows setting enabled status, default mode, initial location enablement, custom settings, templates, and app priorities.

operationId: `PartnerConfig.patchAppPrioritizationPartnerConfig`

**Required to call:** `partnerId` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `partnerId` | path | string | **REQUIRED** | partner Id |
| `data` | body | AppPrioritizationConfigRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Partner id or WifiNetwork does not exist and is not known to Plume; `500` Unhandled API error

#### `DELETE` `/partnerConfig/{partnerId}/qos/appPrioritization/customSetting`
*Set custom setting to default for app prioritization.*

Resets the custom settings for a partner's app prioritization configuration to their default values.

operationId: `PartnerConfig.deleteAppPrioritizationPartnerCustomSetting`

**Required to call:** `partnerId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `partnerId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Partner configuration not found; `500` Unhandled API error

#### `DELETE` `/partnerConfig/{partnerId}/qos/appPrioritization/appPriority`
*Set app priority to default for app prioritization.*

Resets the app priority overrides for a partner's app prioritization configuration to their default values.

operationId: `PartnerConfig.deleteAppPrioritizationPartnerAppPriority`

**Required to call:** `partnerId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `partnerId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Partner configuration not found; `500` Unhandled API error

#### `GET` `/partnerConfig/{id}/captivePortal`
*Get partners captivePortal configs *

Retrieves the captive portal configuration for a partner.
If no configuration exists, a default configuration is built and returned.

operationId: `PartnerConfig.getCaptivePortalConfig`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `500` Unhandled API error

#### `PATCH` `/partnerConfig/{id}/captivePortal`
*Patch a partners captivePortal configs*

Updates the captive portal configuration for a partner, specifically the default language.
If no configuration exists, it will be created.

operationId: `PartnerConfig.updateCaptivePortalConfig`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |
| `data` | body | CaptivePortalConfigRequestDTO | optional |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Partner not found.; `422` Invalid request; `500` Unhandled API error

#### `GET` `/partnerConfig/{id}/featureFlags`
*Get partners feature flags*

Retrieves the feature flags for a partner.
If no configuration exists for the partner, default flags (possibly with deployment-specific overrides) are returned.

operationId: `PartnerConfig.getFeatureFlags`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `500` Unhandled API error

#### `PATCH` `/partnerConfig/{id}/featureFlags`
*Patch a partners feature flags*

Updates the feature flags for a partner.
Validates partner existence, deployment, and ensures all flag values are boolean and field names are valid.

operationId: `PartnerConfig.updateFeatureFlags`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |
| `data` | body | PartnerFeatureFlagsRequestDTO | optional |  |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `403` Forbidden; `404` Partner not found.; `422` Invalid request; `500` Unhandled API error

#### `GET` `/partnerConfig/{id}/machineToMachine`
*Get partners machine to machine information*

Retrieves a partner's machine-to-machine (M2M) configuration details, including M2M ID and existing tokens.
Fails if M2M is not enabled for the partner.

operationId: `PartnerConfig.getMachineToMachine`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Machine to Machine tokens are not enabled for this partner.; `500` Unhandled API error

#### `PUT` `/partnerConfig/{id}/machineToMachine`
*Enable machine to machine token generation for partnerId*

Activates machine-to-machine (M2M) token generation for a partner.
Creates an M2M integration user, assigns roles, and links to the group. Fails if M2M is already active or the group does not exist.

operationId: `PartnerConfig.enableMachineToMachine`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `403` Forbidden; `404` Group for provided partnerId does not exist.; `422` Invalid request; `500` Unhandled API error

#### `DELETE` `/partnerConfig/{id}/machineToMachine`
*Disable machine to machine token generation for partner*

Deactivates machine-to-machine (M2M) token generation for a partner.
This involves deleting the associated M2M customer and their configurations.

operationId: `PartnerConfig.disableMachineToMachine`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `403` Forbidden; `404` Machine to Machine tokens are not enabled for this partner or group not found.; `500` Unhandled API error

#### `POST` `/partnerConfig/{id}/machineToMachine/tokens`
*Generate a new Machine to Machine token for PartnerId*

Generates a new machine-to-machine (M2M) access token for a partner.
Validates token TTL and maximum token limits.

operationId: `PartnerConfig.generateMachineToMachineToken`

**Required to call:** `id` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |
| `data` | body | GenerateM2MTokenRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Machine to Machine tokens are not enabled for this partnerId.; `422` Invalid request; `500` Unhandled API error

#### `DELETE` `/partnerConfig/{id}/machineToMachine/tokens/{tokenId}`
*Delete one of the tokens for the PartnerId*

Deletes a specific machine-to-machine (M2M) access token for a partner.
Fails if M2M is not enabled or the token doesn't exist.

operationId: `PartnerConfig.deleteMachineToMachineToken`

**Required to call:** `id` (path), `tokenId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |
| `tokenId` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful; `401` Authorization failed; `404` Machine to Machine tokens are not enabled for this partner or token not found.; `500` Unhandled API error

#### `GET` `/partnerConfig/{id}/securityPolicy`
*Get partner's default securityPolicy*

Retrieves the default security policy for a partner, including whitelists, blacklists, and other security settings from Councilman.

operationId: `PartnerConfig.getSecurityPolicy`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Partner configuration not found or partner not found.; `500` Unhandled API error

#### `PATCH` `/partnerConfig/{id}/securityPolicy`
*Set partner's default securityPolicy*

Updates a partner's default security policy settings.
Validates input attributes and updates the configuration in Councilman.

operationId: `PartnerConfig.patchSecurityPolicy`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |
| `data` | body | PartnerSecurityPolicyRequestDTO | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/partnerConfig/{id}/platform/appQoe`
*Get the App QoE configuration for a partner.*

Retrieves the App QoE (Quality of Experience) configuration for a specific partner.
Returns the current settings that control application quality of experience monitoring.
If no configuration exists, returns the default configuration.

operationId: `PartnerConfig.getAppQoe`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/partnerConfig/{id}/platform/appQoe`
*Update the App QoE configuration for a partner.*

Updates or creates the App QoE (Quality of Experience) configuration for a specific partner.
Allows setting the configuration that controls application quality of experience monitoring.
The configuration will be validated against the App QoE schema before being applied.

operationId: `PartnerConfig.updateAppQoe`

**Required to call:** `id` (path), `config` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |
| `config` | body | AppQoeConfigRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/partnerConfig/{id}/platform/appQoe`
*Delete the App QoE configuration for a partner.*

Removes the App QoE (Quality of Experience) configuration for a specific partner.
This will reset all App QoE settings to their default values.
The configuration affects how application traffic is monitored and managed for quality of experience.

operationId: `PartnerConfig.deleteAppQoe`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Partner ID |

**Possible responses:** `204` Request was successful

#### `GET` `/partnerConfig/{id}/platform/fronthauls`
*Get the Fronthauls configuration for a partner.*

Retrieves the Fronthauls configuration for a specific partner.
Returns the current settings that control fronthaul network management.
If no configuration exists, returns the default configuration.

operationId: `PartnerConfig.getFronthauls`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/partnerConfig/{id}/platform/fronthauls`
*Update the Fronthauls configuration for a partner.*

Updates or creates the Fronthauls configuration for a specific partner.
Allows setting the configuration that controls fronthaul network management and settings.
The configuration will be validated against the Fronthauls schema before being applied.

operationId: `PartnerConfig.putFronthauls`

**Required to call:** `id` (path), `config` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Partner ID |
| `config` | body | FronthaulConfigRequestDTO | **REQUIRED** | The Fronthauls configuration to apply |

**Possible responses:** `200` Request was successful

#### `DELETE` `/partnerConfig/{id}/platform/fronthauls`
*Delete the Fronthauls configuration for a partner.*

Removes the Fronthauls configuration for a specific partner.
This will reset all Fronthauls settings to their default values.
The configuration affects how fronthaul networks are managed and configured.

operationId: `PartnerConfig.deleteFronthauls`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Partner ID |

**Possible responses:** `204` Request was successful

#### `GET` `/partnerConfig/{id}/platform/speedTest`
*Get the Speed Test configuration for a partner.*

Retrieves the Speed Test configuration for a specific partner.
Returns the current settings that control network speed testing functionality.
If no configuration exists, returns the default configuration.

operationId: `PartnerConfig.getSpeedTest`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/partnerConfig/{id}/platform/speedTest`
*Update the Speed Test configuration for a partner.*

Updates or creates the Speed Test configuration for a specific partner.
Allows setting the configuration that controls network speed testing functionality.
The configuration will be validated against the Speed Test schema before being applied.

operationId: `PartnerConfig.updateSpeedTest`

**Required to call:** `id` (path), `config` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |
| `config` | body | PartnerSpeedTestConfigRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/partnerConfig/{id}/platform/speedTest`
*Delete the Speed Test configuration for a partner.*

Removes the Speed Test configuration for a specific partner.
This will reset all Speed Test settings to their default values.
The configuration controls how speed tests are performed, including frequency and thresholds.

operationId: `PartnerConfig.deleteSpeedTest`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Partner ID |

**Possible responses:** `204` Request was successful

#### `GET` `/partnerConfig/{id}/platform/pcs`
*Get the Pre-CAC Scheduler configuration for a partner.*

Retrieves the Pre-CAC Scheduler configuration for a specific partner.
Returns the current settings that control pre-CAC scheduling and management.
If no configuration exists, returns the default configuration.

operationId: `PartnerConfig.getPreCacScheduler`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/partnerConfig/{id}/platform/pcs`
*Update the Pre-CAC Scheduler configuration for a partner.*

Updates or creates the Pre-CAC Scheduler configuration for a specific partner.
Allows setting the configuration that controls pre-CAC scheduling and management.
The configuration will be validated against the Pre-CAC Scheduler schema before being applied.

operationId: `PartnerConfig.updatePreCacScheduler`

**Required to call:** `id` (path), `config` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |
| `config` | body | PreCacSchedulerConfigRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/partnerConfig/{id}/platform/pcs`
*Delete the Pre-CAC Scheduler configuration for a partner.*

Removes the Pre-CAC Scheduler configuration for a specific partner.
This will reset all Pre-CAC Scheduler settings to their default values.
The configuration affects how pre-CAC scheduling and management is handled.

operationId: `PartnerConfig.deletePreCacScheduler`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `GET` `/partnerConfig/{id}/platform/samKnows`
*Get the Sam Knows configuration for a partner.*

Retrieves the Sam Knows configuration for a specific partner.
Returns the current settings that control Sam Knows monitoring and analytics.
If no configuration exists, returns the default configuration.

operationId: `PartnerConfig.getSamKnows`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Partner ID |

**Possible responses:** `200` Request was successful

#### `PUT` `/partnerConfig/{id}/platform/samKnows`
*Update the Sam Knows configuration for a partner.*

Updates or creates the Sam Knows configuration for a specific partner.
Allows setting the configuration that controls Sam Knows monitoring and analytics.
The configuration will be validated against the Sam Knows schema before being applied.

operationId: `PartnerConfig.updateSamKnows`

**Required to call:** `id` (path), `config` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Partner ID |
| `config` | body | SamKnowsConfigRequestDTO | **REQUIRED** | The Sam Knows configuration to apply |

**Possible responses:** `200` Request was successful

#### `DELETE` `/partnerConfig/{id}/platform/samKnows`
*Delete the Sam Knows configuration for a partner.*

Removes the Sam Knows configuration for a specific partner.
This will reset all Sam Knows settings to their default values.
The configuration affects how Sam Knows monitoring and analytics are handled.

operationId: `PartnerConfig.deleteSamKnows`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Partner ID |

**Possible responses:** `204` Request was successful

#### `GET` `/partnerConfig/{id}/platform/sipAlg`
*Get the SIP ALG configuration for a partner.*

Retrieves the SIP ALG (Application Layer Gateway) configuration for a specific partner.
Returns the current settings that control SIP traffic handling and processing.
If no configuration exists, returns the default configuration.

operationId: `PartnerConfig.getSipAlg`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Partner ID |

**Possible responses:** `200` Request was successful

#### `PUT` `/partnerConfig/{id}/platform/sipAlg`
*Update the SIP ALG configuration for a partner.*

Updates or creates the SIP ALG (Application Layer Gateway) configuration for a specific partner.
Allows setting the configuration that controls SIP traffic handling and processing.
The configuration will be validated against the SIP ALG schema before being applied.

operationId: `PartnerConfig.updateSipAlg`

**Required to call:** `id` (path), `config` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Partner ID |
| `config` | body | SipAlgConfigRequestDTO | **REQUIRED** | The SIP ALG configuration to apply |

**Possible responses:** `200` Request was successful

#### `DELETE` `/partnerConfig/{id}/platform/sipAlg`
*Delete the SIP ALG configuration for a partner.*

Removes the SIP ALG (Application Layer Gateway) configuration for a specific partner.
This will reset all SIP ALG settings to their default values.
The configuration affects how SIP traffic is handled and processed.

operationId: `PartnerConfig.deleteSipAlg`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | Partner ID |

**Possible responses:** `204` Request was successful

#### `GET` `/partnerConfig/{id}/platform/vlanServices`
*Get the VLAN Services configuration for a partner.*

Retrieves the VLAN Services configuration for a specific partner.
Returns the current settings that control VLAN services management.
If no configuration exists, returns the default configuration.

operationId: `PartnerConfig.getVlanServices`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/partnerConfig/{id}/platform/vlanServices`
*Update the VLAN Services configuration for a partner.*

Updates or creates the VLAN Services configuration for a specific partner.
Allows setting the configuration that controls VLAN services management.
The configuration will be validated against the VLAN Services schema before being applied.

operationId: `PartnerConfig.putVlanServices`

**Required to call:** `id` (path), `config` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |
| `config` | body | VlanServicesConfigRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/partnerConfig/{id}/platform/vlanServices`
*Delete the VLAN Services configuration for a partner.*

Removes the VLAN Services configuration for a specific partner.
This will reset all VLAN Services settings to their default values.
The configuration affects how VLAN services are managed and configured.

operationId: `PartnerConfig.deleteVlanService`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `GET` `/partnerConfig/{id}/platform/wag`
*Get the WAG configuration for a partner.*

Retrieves the WAG (Wireless Access Gateway) configuration for a specific partner.
Returns the current settings that control wireless access and gateway services.
If no configuration exists, returns the default configuration.

operationId: `PartnerConfig.getWag`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/partnerConfig/{id}/platform/wag`
*Update the WAG configuration for a partner.*

Updates or creates the WAG (Wireless Access Gateway) configuration for a specific partner.
Allows setting the configuration that controls wireless access and gateway services.
The configuration will be validated against the WAG schema before being applied.

operationId: `PartnerConfig.putWag`

**Required to call:** `id` (path), `config` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |
| `config` | body | WagConfigRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/partnerConfig/{id}/platform/wag`
*Delete the WAG configuration for a partner.*

Removes the WAG (Wireless Access Gateway) configuration for a specific partner.
This will reset all WAG settings to their default values.
The configuration affects how wireless access and gateway services are handled.

operationId: `PartnerConfig.deleteWag`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `GET` `/partnerConfig/{id}/platform/moduleVersionMatrix`
*Get the Module Version Matrix configuration for a cohort.*

Retrieves the Module Version Matrix configuration for a specific cohort or partner.
If no configuration exists, returns the default configuration.

operationId: `PartnerConfig.getModuleVersionMatrix`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `PUT` `/partnerConfig/{id}/platform/moduleVersionMatrix`
*Update the Module Version Matrix for a cohort.*

Sets the module version matrix for a specific cohort or partner.
The configuration will be validated against the Module Version Matrix schema before being applied.

operationId: `PartnerConfig.putModuleVersionMatrix`

**Required to call:** `id` (path), `config` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |
| `config` | body | ModuleVersionMatrixConfigRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `DELETE` `/partnerConfig/{id}/platform/moduleVersionMatrix`
*Delete the Module Version Matrix configuration for a cohort.*

Removes the Module Version Matrix configuration for a specific cohort or partner.
This will reset the Module Version Matrix settings to their default values.

operationId: `PartnerConfig.deleteModuleVersionMatrix`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |

**Possible responses:** `204` Request was successful

#### `GET` `/partnerConfig/{id}/platform`
*Get all Partner Orchestrator configurations for a partner.*

Retrieves all Partner Orchestrator configurations for a specific partner.
Returns a comprehensive set of configurations including all platform settings.
If no configurations exist, returns the default configurations.

operationId: `PartnerConfig.getPartnerOrchestratorConfigs`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/partnerConfig/{id}/homepass/customerSupportConfigurations`
*get homepass customer support configurations*

Retrieves the HomePass customer support configurations for a partner or the default set if 'id' is 'default' or unspecified.
Merges partner-specific settings with cloud defaults.

operationId: `PartnerConfig.getHomepassCustomerSupportConfigurations`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `422` Invalid request; `500` Unhandled API error

#### `PATCH` `/partnerConfig/{id}/homepass/customerSupportConfigurations`
*Patch customer support configurations*

Updates the HomePass customer support configurations for a specific partner or the default set.
Validates configurations before applying.

operationId: `PartnerConfig.patchHomepassCustomerSupportConfigurations`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |
| `data` | body | homepassCustomerSupportConfigurations | optional |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `422` Invalid request; `500` Unhandled API error

#### `GET` `/partnerConfig/{id}/workpass/customerSupportConfigurations`
*Get workpass customer support configurations*

Retrieves the WorkPass customer support configurations for a partner or the default set if 'id' is 'default' or unspecified.
Merges partner-specific settings with cloud defaults and sets deployment-specific webapp URL.

operationId: `PartnerConfig.getWorkpassCustomerSupportConfigurations`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `422` Invalid request; `500` Unhandled API error

#### `PATCH` `/partnerConfig/{id}/workpass/customerSupportConfigurations`
*Patch customer support configurations*

Updates the WorkPass customer support configurations for a specific partner or the default set.
Validates configurations before applying.

operationId: `PartnerConfig.patchWorkpassCustomerSupportConfigurations`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |
| `data` | body | workpassCustomerSupportConfigurations | optional |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `422` Invalid request; `500` Unhandled API error

#### `GET` `/partnerConfig/{id}/captivePortal/terms`
*Get partner Captive Portal Terms of Service document. If the partner does not have a custom terms document, the cloud default is returned.*

Retrieves the Captive Portal Terms and Conditions document for a partner.
If the partner hasn't set custom terms, the cloud's default terms are returned.

operationId: `PartnerConfig.getPartnerCaptivePortalTerms`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Partner configuration not found (default is used as fallback).; `500` Unhandled API error

#### `PATCH` `/partnerConfig/{id}/captivePortal/terms`
*Patch partner Captive Portal Terms and Conditions document*

Updates the Captive Portal Terms and Conditions document for a specific partner.
Cannot edit 'default' partner terms via API.

operationId: `PartnerConfig.patchPartnerCaptivePortalTerms`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |
| `data` | body | PartnerCaptivePortalTermsRequestDTO | optional |  |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Partner configuration not found (will be created if missing).; `422` Invalid request; `500` Unhandled API error

### AuditTrail
Audit trail APIs

#### `GET` `/AuditTrails/getAuditTrail`
*Get Audit Trail for a customer and/or location*

<div><strong>200</strong>: Ok.</div>
<div><strong>401</strong>: Authorization required.</div>
<div><strong>404</strong>: Location id, does not exist.</div>
<div><strong>500</strong>: Internal server error.</div>

operationId: `AuditTrail.getAuditTrail`

**Required to call:** `customerId` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `customerId` | query | string | **REQUIRED** | Customer Id |
| `locationId` | query | string | optional | Location ID |
| `partnerIds` | query | string | optional | Partner Id |

**Possible responses:** `200` Request was successful

### Token
#### `POST` `/Tokens/refresh`
*Refreshes a token set.*

This endpoint is used to refresh a token set. The token sent in the request body must be a refresh token.
The response will contain a new access token and a new refresh token.
The old refresh token will be invalidated.

operationId: `Token.refresh`

**Required to call:** `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `data` | body | RefreshTokenRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `403` Forbidden; `500` Unhandled API error

#### `POST` `/Tokens/revoke`
*Revokes a token.*

This endpoint is used to revoke a token.
The token sent in the request body can be an access token or a refresh token.
The token will be invalidated.

If the token is a refresh token, the access token associated with it will also be invalidated.

operationId: `Token.revoke`

**Required to call:** `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `data` | body | RevokeTokenRequestDTO | **REQUIRED** |  |

**Possible responses:** `204` Request was successful; `400` Incorrect request; `401` Authorization failed; `500` Unhandled API error

#### `POST` `/Tokens/info`
*Returns information about a token.*

This endpoint is used to get information about a token.
The token sent in the request body must be an access token.

operationId: `Token.info`

**Required to call:** `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `data` | body | TokenInfoRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `500` Unhandled API error

#### `POST` `/Tokens/odm-admin-location-access-token`
*Mints an ODM Admin token for a location.*

This endpoint is used to mint an ODM Admin token for a location.

This endpoint is only accessible to the MICE tokens.
If the location does not belong to the partner, a 403 error will be returned.

operationId: `Token.mintODMAdminTokenForLocation`

**Required to call:** `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `data` | body | MintODMAdminTokenForLocationRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `403` Forbidden; `404` There are no Locations with the ID "{id}"; `500` Unhandled API error

### NodeModel
#### `GET` `/NodeModels/{id}`
*Get a node model by ID*

Retrieves a specific node model by its unique identifier.

If the node model is not found, the API will return a 404 error.
Use this endpoint when you need to fetch detailed information about a specific node model.

operationId: `NodeModel.getNodeModelById`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | The unique node model string (eg. PP203X) |

**Possible responses:** `200` Request was successful; `400` Missing required argument; `401` Authorization failed; `404` Node Model not found; `500` Unhandled API error

#### `DELETE` `/NodeModels/{id}`
*Delete a node model by ID*

Permanently deletes a node model from the system.

If the node model is not found, the API will return a 404 error.
Upon successful deletion, the API will return a success message.
This operation cannot be undone - use with caution.

operationId: `NodeModel.deleteNodeModel`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | The unique node model string (eg. PP203X) |

**Possible responses:** `200` Request was successful; `400` Missing required argument; `401` Authorization failed; `404` Node Model not found; `500` Unhandled API error

#### `PATCH` `/NodeModels/{id}`
*Update a node model by ID*

Updates an existing node model with the provided data.

Only the fields included in the request body will be updated.
If the node model is not found, the API will return a 404 error.
The response will contain the updated node model object.

operationId: `NodeModel.updateNodeModel`

**Required to call:** `id` (path), `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** | The unique node model string (eg. PP203X) |
| `data` | body | PatchNodeModelRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `404` Node Model not found; `422` Invalid request; `500` Unhandled API error

#### `POST` `/NodeModels`
*Create a new node model*

Creates a new node model with the provided data.

The request body should contain all required fields for the node model.
Upon successful creation, the API will return the newly created node model object.
Validation errors will be returned if the provided data is invalid.

operationId: `NodeModel.createNodeModel`

**Required to call:** `data` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `data` | body | PostNodeModelRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `422` Invalid request; `500` Unhandled API error

### ContentCategory
Content Category APIs

#### `GET` `/ContentCategories/recategorizations/domains`
*List domain recategorization requests (paged).*

operationId: `ContentCategory.listDomainRecategorizations`

**Required to call:** none

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `domain` | query | string | optional |  |
| `status` | query | string | optional |  |
| `startCreationTime` | query | string | optional |  |
| `endCreationTime` | query | string | optional |  |
| `page` | query | number | optional |  |
| `size` | query | number | optional |  |
| `sort` | query | string | optional |  |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `500` Unhandled API error

#### `POST` `/ContentCategories/recategorizations/domains`
*Submit a domain recategorization request.*

operationId: `ContentCategory.recategorizeDomain`

**Required to call:** `body` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `body` | body | PostDomainRecategorizationRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `500` Unhandled API error

#### `GET` `/ContentCategories/recategorizations/ips`
*List IP recategorization requests (paged).*

operationId: `ContentCategory.listIpRecategorizations`

**Required to call:** none

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `ipAddress` | query | string | optional |  |
| `status` | query | string | optional |  |
| `startCreationTime` | query | string | optional |  |
| `endCreationTime` | query | string | optional |  |
| `page` | query | number | optional |  |
| `size` | query | number | optional |  |
| `sort` | query | string | optional |  |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `500` Unhandled API error

#### `POST` `/ContentCategories/recategorizations/ips`
*Submit an IP recategorization request.*

operationId: `ContentCategory.recategorizeIp`

**Required to call:** `body` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `body` | body | PostIpRecategorizationRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `500` Unhandled API error

#### `GET` `/ContentCategories/recategorizations/urls`
*List URL recategorization requests (paged).*

operationId: `ContentCategory.listUrlRecategorizations`

**Required to call:** none

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `url` | query | string | optional |  |
| `status` | query | string | optional |  |
| `startCreationTime` | query | string | optional |  |
| `endCreationTime` | query | string | optional |  |
| `page` | query | number | optional |  |
| `size` | query | number | optional |  |
| `sort` | query | string | optional |  |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `500` Unhandled API error

#### `POST` `/ContentCategories/recategorizations/urls`
*Submit a URL recategorization request.*

operationId: `ContentCategory.recategorizeUrl`

**Required to call:** `body` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `body` | body | PostUrlRecategorizationRequestDTO | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `500` Unhandled API error

#### `GET` `/ContentCategories/recategorizations/domains/{requestId}`
*Get the status of a domain recategorization request.*

operationId: `ContentCategory.getDomainRecategorization`

**Required to call:** `requestId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `requestId` | path | string | **REQUIRED** | Recategorization request id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Not Found; `500` Unhandled API error

#### `GET` `/ContentCategories/recategorizations/ips/{requestId}`
*Get the status of an IP recategorization request.*

operationId: `ContentCategory.getIpRecategorization`

**Required to call:** `requestId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `requestId` | path | string | **REQUIRED** | Recategorization request id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Not Found; `500` Unhandled API error

#### `GET` `/ContentCategories/recategorizations/urls/{requestId}`
*Get the status of a URL recategorization request.*

operationId: `ContentCategory.getUrlRecategorization`

**Required to call:** `requestId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `requestId` | path | string | **REQUIRED** | Recategorization request id |

**Possible responses:** `200` Request was successful; `401` Authorization failed; `404` Not Found; `500` Unhandled API error

#### `POST` `/ContentCategories/domains/lookup`
*Batch lookup of domain categories.*

operationId: `ContentCategory.lookupDomains`

**Required to call:** `body` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `body` | body | array | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `400` Incorrect request; `401` Authorization failed; `500` Unhandled API error

#### `GET` `/ContentCategories/categoryFilters`
*Get content filter categories with category metadata, safe-search ids, fqdn allow/deny, priority, and version.*

operationId: `ContentCategory.categoryFilters`

**Parameters:** none

**Possible responses:** `200` Request was successful; `401` Authorization failed; `500` Unhandled API error

#### `POST` `/ContentCategories/cache/invalidations/domains`
*Invalidate Nagra content category cache entries for a batch of domains.*

operationId: `ContentCategory.invalidateDomainCache`

**Required to call:** `body` (body)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `body` | body | array | **REQUIRED** |  |

**Possible responses:** `202` Request was successful; `400` Incorrect request; `401` Authorization failed; `500` Unhandled API error

---
## Reports API (v1.0.0)
Base URL: `https://piranha-gamma.prod.us-west-2.aws.plumenet.io/reports`

### Customer
#### `GET` `/Customers/{id}/locations/{locationId}/optimizeRequests/{optimizeRequestId}`
*Find a model instance by {{id}} from the data source*

**Required to call:** `id` (path), `locationId` (path), `optimizeRequestId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | location id |
| `optimizeRequestId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Success, object returned; `401` Authorization required; `404` Location id or model id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/optimizeResponses/{optimizeResponseId}`
*Find a model instance by {{id}} from the data source*

**Required to call:** `id` (path), `locationId` (path), `optimizeResponseId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | location id |
| `optimizeResponseId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Success, object returned; `401` Authorization required; `404` Location id or model id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/topologyChangeResults/{topologyChangeResultId}`
*Find a model instance by {{id}} from the data source*

**Required to call:** `id` (path), `locationId` (path), `topologyChangeResultId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | location id |
| `topologyChangeResultId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Success, object returned; `401` Authorization required; `404` Location id or model id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/optimizeRequests`
*Find all instances of the model.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | location id |
| `order` | query | string | optional | desc \|\| asc |
| `limit` | query | number($double) | optional | 1000 max for deep:false and 10 max for deep:true |
| `startAt` | query | string | optional | find objects after this value |
| `deep` | query | boolean | optional | deep:true to receive inflated objects, else defaults to list of object ids |
| `endAt` | query | string | optional | find objects before this value |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/optimizeResponses`
*Find all instances of the model.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | location id |
| `order` | query | string | optional | desc \|\| asc |
| `limit` | query | number($double) | optional | 1000 max for deep:false and 10 max for deep:true |
| `startAt` | query | string | optional | find objects after this value |
| `deep` | query | boolean | optional | deep:true to receive inflated objects, else defaults to list of object ids |
| `endAt` | query | string | optional | find objects before this value |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/topologyChangeResults`
*Find all instances of the model.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | location id |
| `order` | query | string | optional | desc \|\| asc |
| `limit` | query | number($double) | optional | 1000 max for deep:false and 10 max for deep:true |
| `startAt` | query | string | optional | find objects after this value |
| `deep` | query | boolean | optional | deep:true to receive inflated objects, else defaults to list of object ids |
| `endAt` | query | string | optional | find objects before this value |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/results`
*Node speed test result for a particular location.*

**Required to call:** `id` (path), `nodeId` (path), `locationId` (path), `granularity` (query), `limit` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `nodeId` | path | string($JSON) | **REQUIRED** |  |
| `locationId` | path | string($JSON) | **REQUIRED** |  |
| `granularity` | query | string | **REQUIRED** | days/hours/minutes |
| `limit` | query | number($double) | **REQUIRED** | X # of days/hours/minutes |
| `showFailedSpeedTests` | query | boolean | optional | Shows failed speed tests |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/results/{requestId}`
*Get single node speed test result by requestId.*

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path), `requestId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string($JSON) | **REQUIRED** |  |
| `nodeId` | path | string($JSON) | **REQUIRED** |  |
| `requestId` | path | string($JSON) | **REQUIRED** |  |

**Possible responses:** `200` Success; `401` Authorization required; `404` Node speed test not found; `500` Failed while fetching node speed test result from DB

#### `GET` `/Customers/{id}/locations/{locationId}/wanSaturation`
*Get WAN saturation and chart data for a location.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | location id |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/wanStats`
*aggregate all wan stats for a particular location.*

**Required to call:** `id` (path), `locationId` (path), `period` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `period` | query | string | **REQUIRED** | daily, weekly, monthly |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `422` invalid 'period' error; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/wanStatsLiveModeStream`
*query all wan stats live mode for a particular location.*

**Required to call:** `id` (path), `locationId` (path), `startTime` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `startTime` | query | string | **REQUIRED** | the startTime is in the past. |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `422` invalid 'period' error; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/appResults`
*speed test result aggregation for a particular location.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string($JSON) | **REQUIRED** |  |
| `timezone` | query | string | optional |  |
| `recentSpeedTest` | query | string($JSON) | optional |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/bandSteeringStats`
*Device band steering stats with all nodes for a particular MAC address.*

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | location id of devices and nodes |
| `mac` | path | string | **REQUIRED** | mac id of device |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number($double) | optional | X # of days/hours/minutes |
| `start` | query | number($double) | optional | number of milliseconds elapsed since 1 January 1970 00:00:00 UTC. Defaults to now - (limit * granularity) |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/bandSteeringSummary`
*Device band steering stats with all nodes for a particular MAC address.*

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | location id of devices and nodes |
| `mac` | path | string | **REQUIRED** | mac id of device |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/clientSteeringSummary`
*Device client steering stats with all nodes for a particular MAC address.*

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | location id of devices and nodes |
| `mac` | path | string | **REQUIRED** | mac id of device |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/clientSteeringStats`
*Device client steering stats with all nodes for a particular MAC address.*

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | location id of devices and nodes |
| `mac` | path | string | **REQUIRED** | mac id of device |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number($double) | optional | X # of days/hours/minutes |
| `start` | query | number($double) | optional | number of milliseconds elapsed since 1 January 1970 00:00:00 UTC. Defaults to now - (limit * granularity) |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/bandSteeringStats`
*Location band steering stats.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | location id |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number($double) | optional | X # of days/hours/minutes |
| `start` | query | number($double) | optional | number of milliseconds elapsed since 1 January 1970 00:00:00 UTC. Defaults to now - (limit * granularity) |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/clientSteeringStats`
*Location client steering stats.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | location id |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number($double) | optional | X # of days/hours/minutes |
| `start` | query | number($double) | optional | number of milliseconds elapsed since 1 January 1970 00:00:00 UTC. Defaults to now - (limit * granularity) |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/optimizationSummary`
*Location optimization Summary in 24 hours.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | location id |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/broadbandEfficiencyAlert`
*Location optimization Summary in 24 hours.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | location id |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/rssi`
*Device RSSI graph array for a particular MAC address.*

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `mac` | path | string | **REQUIRED** | mac id of client |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number($double) | optional | X # of days/hours/minutes |
| `start` | query | number($double) | optional | number of milliseconds elapsed since 1 January 1970 00:00:00 UTC. Defaults to now - (limit * granularity) |

**Possible responses:** `200` Request was successful

Response example (200):
```json
{
  "statsDateRange": [
    {
      "start": [
        "2026-08-13T20:45:26.798Z"
      ],
      "end": [
        "2026-08-13T20:45:26.798Z"
      ],
      "id": 0
    }
  ],
  "2g": {},
  "5g": {},
  "6g": {},
  "id": 0
}
```

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/radio/{radio}/bandwidth`
*Radio transmitted and received bandwidth graph array for a particular Node WiFi Radio.*

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path), `radio` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `nodeId` | path | string | **REQUIRED** |  |
| `radio` | path | string | **REQUIRED** | 5G or 2.4G or 6G |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number($double) | optional | X # of days/hours/minutes |
| `start` | query | number($double) | optional | number of milliseconds elapsed since 1 January 1970 00:00:00 UTC. Defaults to now - (limit * granularity) |

**Possible responses:** `200` Request was successful

Response example (200):
```json
{
  "statsDateRange": [
    {
      "start": [
        "2026-08-13T20:45:26.824Z"
      ],
      "end": [
        "2026-08-13T20:45:26.824Z"
      ],
      "id": 0
    }
  ],
  "2g": [
    {
      "timestamp": "2026-08-13T20:45:26.824Z",
      "value": 0
    }
  ],
  "5g": [
    {
      "timestamp": "2026-08-13T20:45:26.824Z",
      "value": 0
    }
  ],
  "6g": [
    {
      "timestamp": "2026-08-13T20:45:26.824Z",
      "value": 0
    }
  ],
  "id": 0
}
```

#### `GET` `/Customers/{id}/locations/{locationId}/alarm`
*Radio alarm history graph array for a particular Node WiFi Radio.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number($double) | optional | X # of days/hours/minutes |
| `start` | query | number($double) | optional | number of milliseconds elapsed since 1 January 1970 00:00:00 UTC. Defaults to now - (limit * granularity) |

**Possible responses:** `200` Request was successful

Response example (200):
```json
{
  "statsDateRange": [
    {
      "start": [
        "2026-08-13T20:45:26.841Z"
      ],
      "end": [
        "2026-08-13T20:45:26.841Z"
      ],
      "id": 0
    }
  ],
  "deviceAlarm": [
    {
      "timestamp": "2026-08-13T20:45:26.841Z",
      "value": 0
    }
  ],
  "podAlarm": [
    {
      "timestamp": "2026-08-13T20:45:26.841Z",
      "value": 0
    }
  ],
  "id": 0
}
```

#### `GET` `/Customers/{id}/locations/{locationId}/alarmSummary`
*Radio alarm history graph array for a particular Node WiFi Radio.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/node/{nodeId}/alarms`
*Pod/Device alarm history graph array for a particular MAC address/Pod id.*

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `nodeId` | path | string | **REQUIRED** | mac id of device or pod id |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number($double) | optional | X # of days/hours/minutes |
| `start` | query | number($double) | optional | number of milliseconds elapsed since 1 January 1970 00:00:00 UTC. Defaults to now - (limit * granularity) |

**Possible responses:** `200` Request was successful

Response example (200):
```json
{
  "statsDateRange": [
    {
      "start": [
        "2026-08-13T20:45:26.870Z"
      ],
      "end": [
        "2026-08-13T20:45:26.870Z"
      ],
      "id": 0
    }
  ],
  "2g": [
    {
      "timestamp": "2026-08-13T20:45:26.870Z",
      "value": 0
    }
  ],
  "5g": [
    {
      "timestamp": "2026-08-13T20:45:26.870Z",
      "value": 0
    }
  ],
  "6g": [
    {
      "timestamp": "2026-08-13T20:45:26.870Z",
      "value": 0
    }
  ],
  "id": 0
}
```

#### `GET` `/Customers/{id}/locations/{locationId}/nodeDevice/alarms`
*Pod/Device alarm history graph array for a particular MAC address/Pod id.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number($double) | optional | X # of days/hours/minutes |
| `start` | query | number($double) | optional | number of milliseconds elapsed since 1 January 1970 00:00:00 UTC. Defaults to now - (limit * granularity) |

**Possible responses:** `200` Request was successful

Response example (200):
```json
{
  "statsDateRange": [
    {
      "start": [
        "2026-08-13T20:45:26.887Z"
      ],
      "end": [
        "2026-08-13T20:45:26.887Z"
      ],
      "id": 0
    }
  ],
  "alarmDevices": [
    {
      "timestamp": "2026-08-13T20:45:26.887Z",
      "value": 0
    }
  ],
  "alarmPods": [
    {
      "timestamp": "2026-08-13T20:45:26.887Z",
      "value": 0
    }
  ],
  "alarmIds": [
    "string"
  ],
  "id": 0
}
```

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/radio/{radio}/alarms`
*Radio alarm history graph array for a particular Node WiFi Radio.*

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path), `radio` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `nodeId` | path | string | **REQUIRED** |  |
| `radio` | path | string | **REQUIRED** | 5G or 2.4G or 6G |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number($double) | optional | X # of days/hours/minutes |
| `start` | query | number($double) | optional | number of milliseconds elapsed since 1 January 1970 00:00:00 UTC. Defaults to now - (limit * granularity) |

**Possible responses:** `200` Request was successful

Response example (200):
```json
{
  "statsDateRange": [
    {
      "start": [
        "2026-08-13T20:45:26.911Z"
      ],
      "end": [
        "2026-08-13T20:45:26.911Z"
      ],
      "id": 0
    }
  ],
  "2g": [
    {
      "timestamp": "2026-08-13T20:45:26.911Z",
      "value": 0
    }
  ],
  "5g": [
    {
      "timestamp": "2026-08-13T20:45:26.911Z",
      "value": 0
    }
  ],
  "6g": [
    {
      "timestamp": "2026-08-13T20:45:26.911Z",
      "value": 0
    }
  ],
  "id": 0
}
```

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/radio/{radio}/wifiCapacity`
*Radio WiFi Capacity graph array for a particular Node WiFi Radio.*

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path), `radio` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `nodeId` | path | string | **REQUIRED** |  |
| `radio` | path | string | **REQUIRED** | 5G or 2.4G or 6G |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number($double) | optional | X # of days/hours/minutes |
| `start` | query | number($double) | optional | number of milliseconds elapsed since 1 January 1970 00:00:00 UTC. Defaults to now - (limit * granularity) |

**Possible responses:** `200` Request was successful

Response example (200):
```json
{
  "statsDateRange": [
    {
      "start": [
        "2026-08-13T20:45:26.936Z"
      ],
      "end": [
        "2026-08-13T20:45:26.936Z"
      ],
      "id": 0
    }
  ],
  "2g": [
    {
      "timestamp": "2026-08-13T20:45:26.936Z",
      "value": 0
    }
  ],
  "5g": [
    {
      "timestamp": "2026-08-13T20:45:26.936Z",
      "value": 0
    }
  ],
  "6g": [
    {
      "timestamp": "2026-08-13T20:45:26.936Z",
      "value": 0
    }
  ],
  "id": 0
}
```

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/{sourceId}/edges/{targetId}/edgePhy`
*WiFi link PHY rate graph array for a particular Node-to-Node or Node-to-Device link.*

**Required to call:** `id` (path), `locationId` (path), `sourceId` (path), `targetId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `sourceId` | path | string | **REQUIRED** |  |
| `targetId` | path | string | **REQUIRED** |  |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number($double) | optional | X # of days/hours/minutes |
| `start` | query | number($double) | optional | number of milliseconds elapsed since 1 January 1970 00:00:00 UTC. Defaults to now - (limit * granularity) |

**Possible responses:** `200` Request was successful

Response example (200):
```json
{
  "statsDateRange": [
    {
      "start": [
        "2026-08-13T20:45:26.958Z"
      ],
      "end": [
        "2026-08-13T20:45:26.958Z"
      ],
      "id": 0
    }
  ],
  "2g": [
    {
      "timestamp": "2026-08-13T20:45:26.958Z",
      "value": 0
    }
  ],
  "5g": [
    {
      "timestamp": "2026-08-13T20:45:26.958Z",
      "value": 0
    }
  ],
  "6g": [
    {
      "timestamp": "2026-08-13T20:45:26.958Z",
      "value": 0
    }
  ],
  "id": 0
}
```

#### `GET` `/Customers/{id}/locations/{locationId}/edgesHistory`
*WiFi link PHY rate graph array for a particular Node-to-Node or Node-to-Device link.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number($double) | optional | X # of days/hours/minutes |
| `start` | query | number($double) | optional | number of milliseconds elapsed since 1 January 1970 00:00:00 UTC. Defaults to now - (limit * granularity) |

**Possible responses:** `200` Request was successful

Response example (200):
```json
{
  "statsDateRange": [
    {
      "start": [
        "2026-08-13T20:45:26.976Z"
      ],
      "end": [
        "2026-08-13T20:45:26.976Z"
      ],
      "id": 0
    }
  ],
  "2g": [
    {
      "timestamp": "2026-08-13T20:45:26.976Z",
      "value": 0
    }
  ],
  "5g": [
    {
      "timestamp": "2026-08-13T20:45:26.976Z",
      "value": 0
    }
  ],
  "6g": [
    {
      "timestamp": "2026-08-13T20:45:26.976Z",
      "value": 0
    }
  ],
  "id": 0
}
```

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/radio/{radio}/channelUtilization`
*Radio interference and channel utilization graph array for a particular Node WiFi Radio.*

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path), `radio` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `nodeId` | path | string | **REQUIRED** |  |
| `radio` | path | string | **REQUIRED** | 5G or 2.4G or 6G |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number($double) | optional | X # of days/hours/minutes |
| `start` | query | number($double) | optional | number of milliseconds elapsed since 1 January 1970 00:00:00 UTC. Defaults to now - (limit * granularity) |

**Possible responses:** `200` Request was successful

Response example (200):
```json
{
  "statsDateRange": [
    {
      "start": [
        "2026-08-13T20:45:26.998Z"
      ],
      "end": [
        "2026-08-13T20:45:26.998Z"
      ],
      "id": 0
    }
  ],
  "2g": [
    {
      "timestamp": "2026-08-13T20:45:26.998Z",
      "value": 0
    }
  ],
  "5g": [
    {
      "timestamp": "2026-08-13T20:45:26.998Z",
      "value": 0
    }
  ],
  "6g": [
    {
      "timestamp": "2026-08-13T20:45:26.998Z",
      "value": 0
    }
  ],
  "id": 0
}
```

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/alarms`
*Device alarm history graph array for a particular MAC address.*

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `mac` | path | string | **REQUIRED** | mac id of device |
| `coverageAlarmThreshold` | query | string | optional | a coverage alarm will be returned (value=1) when rssi_alarm_penalty_count >= this value |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number($double) | optional | X # of days/hours/minutes |
| `start` | query | number($double) | optional | number of milliseconds elapsed since 1 January 1970 00:00:00 UTC. Defaults to now - (limit * granularity) |

**Possible responses:** `200` Request was successful

Response example (200):
```json
{
  "statsDateRange": [
    {
      "start": [
        "2026-08-13T20:45:27.021Z"
      ],
      "end": [
        "2026-08-13T20:45:27.021Z"
      ],
      "id": 0
    }
  ],
  "2g": [
    {
      "timestamp": "2026-08-13T20:45:27.021Z",
      "value": 0
    }
  ],
  "5g": [
    {
      "timestamp": "2026-08-13T20:45:27.021Z",
      "value": 0
    }
  ],
  "6g": [
    {
      "timestamp": "2026-08-13T20:45:27.021Z",
      "value": 0
    }
  ],
  "id": 0
}
```

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/bandwidth`
*Device transmitted and received bandwidth graph array for a particular MAC address.*

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `mac` | path | string | **REQUIRED** | mac id of device |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number($double) | optional | X # of days/hours/minutes |
| `start` | query | number($double) | optional | number of milliseconds elapsed since 1 January 1970 00:00:00 UTC. Defaults to now - (limit * granularity) |

**Possible responses:** `200` Request was successful

Response example (200):
```json
{
  "statsDateRange": [
    {
      "start": [
        "2026-08-13T20:45:27.041Z"
      ],
      "end": [
        "2026-08-13T20:45:27.041Z"
      ],
      "id": 0
    }
  ],
  "transmitted": [
    {
      "timestamp": "2026-08-13T20:45:27.041Z",
      "value": 0
    }
  ],
  "received": [
    {
      "timestamp": "2026-08-13T20:45:27.041Z",
      "value": 0
    }
  ],
  "id": 0
}
```

#### `GET` `/Customers/{id}/locations/{locationId}/monthlyReport`
*Monthly usage summary report based on location*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/neighborReport`
*get the neighbor report for a particular location.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/chartData`
*Device average data consumption(24hour/7day/30day) for a particular MAC address.*

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `mac` | path | string | **REQUIRED** | mac id of device |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/dashboard`
*Daily/Weekly/Monthly device usage summary report based on location*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `macs` | query | string($JSON) | optional | mac list of all devices in the location |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/topologyChanges`
*Find all instances of the model.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `order` | query | string | optional | desc \|\| asc |
| `limit` | query | number($double) | optional | 1000 max for deep:false and 10 max for deep:true |
| `startAt` | query | string | optional | find objects after this value |
| `endAt` | query | string | optional | find objects before this value |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/clientSteeringTriggers`
*Find all instances of the model.*

**Required to call:** `id` (path), `mac` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `mac` | path | string | **REQUIRED** |  |
| `locationId` | path | string | **REQUIRED** |  |
| `order` | query | string | optional | desc \|\| asc |
| `limit` | query | number($double) | optional | 1000 max for deep:false and 10 max for deep:true |
| `startAt` | query | string | optional | find objects after this value |
| `endAt` | query | string | optional | find objects before this value |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/hotspotSteeringEvents`
*Chronological list of per-event Hotspot (5G.11 / HS 2.0) steering events for a location. Each row carries the unified soft/hard event payload (btm summary, steer result, link SNR with hex link/BSSID).*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location id. |
| `startAt` | query | string | optional | Window start (ISO-8601). Defaults to endAt - 24h. |
| `endAt` | query | string | optional | Window end (ISO-8601). Defaults to now. |
| `limit` | query | number($double) | optional | Max number of events to return. |
| `order` | query | string | optional | Timestamp ordering: asc \| desc. |
| `mac` | query | string | optional | Optional client MAC filter (any case, with or without colons). |

**Possible responses:** `200` Request was successful

Response example (200):
```json
[
  {}
]
```

#### `GET` `/Customers/{id}/locations/{locationId}/hotspotDailyStats`
*Daily aggregated Hotspot (5G.11 / HS 2.0) stats for a location. Returns one row per UTC date with bytes, client counts, steering event totals and per-outcome steering breakdown.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location id. |
| `startAt` | query | string | optional | Window start (ISO-8601 or YYYY-MM-DD). Defaults to endAt - 7d. |
| `endAt` | query | string | optional | Window end (ISO-8601 or YYYY-MM-DD). Defaults to now. |
| `limit` | query | number($double) | optional | Max number of daily rows to return. |
| `order` | query | string | optional | Date ordering: asc \| desc. |

**Possible responses:** `200` Request was successful

Response example (200):
```json
[
  {}
]
```

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/hotspotDailyStats`
*Daily aggregated Hotspot (5G.11 / HS 2.0) stats for a specific device at a location. Returns one row per UTC date with bytes, connected duration and per-device steering totals.*

**Required to call:** `id` (path), `mac` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `mac` | path | string | **REQUIRED** | Client MAC (any case, colons or dashes). |
| `locationId` | path | string | **REQUIRED** | Location id. |
| `startAt` | query | string | optional | Window start (ISO-8601 or YYYY-MM-DD). Defaults to endAt - 7d. |
| `endAt` | query | string | optional | Window end (ISO-8601 or YYYY-MM-DD). Defaults to now. |
| `limit` | query | number($double) | optional | Max number of daily rows to return. |
| `order` | query | string | optional | Date ordering: asc \| desc. |

**Possible responses:** `200` Request was successful

Response example (200):
```json
[
  {}
]
```

#### `GET` `/Customers/{id}/locations/{locationId}/firmwareUpgrades`
*Find all instances of the model.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `order` | query | string | optional | desc \|\| asc |
| `limit` | query | number($double) | optional | 1000 max for deep:false and 10 max for deep:true |
| `startAt` | query | string | optional | find objects after this value |
| `endAt` | query | string | optional | find objects before this value |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/firmwareUpgrades`
*Find all instances of the model.*

**Required to call:** `id` (path), `nodeId` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `nodeId` | path | string | **REQUIRED** |  |
| `locationId` | path | string | **REQUIRED** |  |
| `order` | query | string | optional | desc \|\| asc |
| `limit` | query | number($double) | optional | 1000 max for deep:false and 10 max for deep:true |
| `startAt` | query | string | optional | find objects after this value |
| `endAt` | query | string | optional | find objects before this value |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/qoe/liveModeStream`
*Device or pod QoE live mode data.*

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `nodeId` | path | string | **REQUIRED** | mac address or pod id |
| `mac` | query | string | optional | mac address or pod id |
| `startTime` | query | number($double) | optional | start timestamp |
| `timestampISOFormat` | query | boolean | optional | either timestamp utc number or ISO string |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/qoe/liveModeStream`
*Device or pod QoE live mode data.*

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `mac` | path | string | **REQUIRED** | mac address or pod id |
| `nodeId` | query | string | optional | mac address or pod id |
| `startTime` | query | number($double) | optional | start timestamp |
| `timestampISOFormat` | query | boolean | optional | either timestamp utc number or ISO string |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/nodePlacement/livePlugPointAssessment`
*Live plug assessment.*

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `mac` | path | string | **REQUIRED** | mac address of a device doing the probe |
| `startTime` | query | number($double) | optional | start timestamp |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/nodePlacement/livePlugDataWithSession`
*Live plug data (all rows in the time window, optional session filter).*

**Required to call:** `id` (path), `locationId` (path), `mac` (path), `startTime` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `mac` | path | string | **REQUIRED** | mac address of a device doing the probe |
| `startTime` | query | string | **REQUIRED** | start time (UTC ISO 8601 date-time) |
| `endTime` | query | string | optional | end time (UTC ISO 8601 date-time; optional; defaults to now) |
| `sessionId` | query | string | optional | session id (optional, any string value) |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/nodePlacement/sessionStatus`
*Placement session engagement timestamps per status (aggregated from placement_session_status).*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `sessionId` | query | string | optional | placement session id (optional; if omitted, all sessions for the location are returned) |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/placement-recommendations`
*Pod placement recommendation timeline for a location, joined with placement_session_status for userAction.*

**Required to call:** `id` (path), `locationId` (path), `startAt` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `startAt` | query | string | **REQUIRED** | ISO UTC date; return records with createdAt at or after this timestamp |
| `limit` | query | number($double) | optional | maximum number of results (default 100) |
| `order` | query | string | optional | asc or desc by createdAt (default desc) |

**Possible responses:** `200` Success; `400` startAt is missing or invalid; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

Response example (200):
```json
[
  {}
]
```

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/qoe/liveModeStreamV2`
*Pod QoE live mode data with MLO support.*

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `nodeId` | path | string | **REQUIRED** | mac address or pod id |
| `mac` | query | string | optional | mac address or pod id |
| `startTime` | query | number($double) | optional | start timestamp |
| `timestampISOFormat` | query | boolean | optional | either timestamp utc number or ISO string |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/qoe/liveModeStreamV2`
*Device QoE live mode data with MLO support.*

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `mac` | path | string | **REQUIRED** | mac address or pod id |
| `nodeId` | query | string | optional | mac address or pod id |
| `startTime` | query | number($double) | optional | start timestamp |
| `timestampISOFormat` | query | boolean | optional | either timestamp utc number or ISO string |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/qoe/superLiveModeStream`
*Device or pod QoE super live mode data.*

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `nodeId` | path | string | **REQUIRED** | mac address or pod id |
| `mac` | query | string | optional | mac address or pod id |
| `startTime` | query | number($double) | optional | start timestamp |
| `timestampISOFormat` | query | boolean | optional | either timestamp utc number or ISO string |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/qoe/superLiveModeStream`
*Device or pod QoE super live mode data.*

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `mac` | path | string | **REQUIRED** | mac address or pod id |
| `nodeId` | query | string | optional | mac address or pod id |
| `startTime` | query | number($double) | optional | start timestamp |
| `timestampISOFormat` | query | boolean | optional | either timestamp utc number or ISO string |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/qoe/superLiveModeStreamV2`
*Device or pod QoE super live mode data with MLO support.*

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `nodeId` | path | string | **REQUIRED** | mac address or pod id |
| `mac` | query | string | optional | mac address or pod id |
| `startTime` | query | number($double) | optional | start timestamp |
| `timestampISOFormat` | query | boolean | optional | either timestamp utc number or ISO string |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/qoe/superLiveModeStreamV2`
*Device or pod QoE super live mode data with MLO support.*

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `mac` | path | string | **REQUIRED** | mac address or pod id |
| `nodeId` | query | string | optional | mac address or pod id |
| `startTime` | query | number($double) | optional | start timestamp |
| `timestampISOFormat` | query | boolean | optional | either timestamp utc number or ISO string |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/qoeMetrics`
*Device or pod QoE 15 minutes data.*

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `nodeId` | path | string | **REQUIRED** | pod id |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number($double) | optional | X # of days/hours/minutes |
| `timestampISOFormat` | query | boolean | optional | either timestamp utc number or ISO string |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/qoeMetrics`
*Device or pod QoE 15 minutes data.*

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `mac` | path | string | **REQUIRED** | device mac address |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number($double) | optional | X # of days/hours/minutes |
| `timestampISOFormat` | query | boolean | optional | either timestamp utc number or ISO string |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/qoeMetricsV2`
*Device QoE metrics with MLO support.*

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `mac` | path | string | **REQUIRED** | device mac address |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number($double) | optional | X # of days/hours/minutes |
| `timestampISOFormat` | query | boolean | optional | either timestamp utc number or ISO string |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location or device not found

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/qoeMetricsV2`
*Pod QoE metrics with MLO support.*

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `nodeId` | path | string | **REQUIRED** | nodeId |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number($double) | optional | X # of days/hours/minutes |
| `timestampISOFormat` | query | boolean | optional | either timestamp utc number or ISO string |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location or device not found

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/utilizationMetrics`
*returns utilization metrics with time series grouped by freqband.*

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `nodeId` | path | string | **REQUIRED** | pod id |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number($double) | optional | X # of days/hours/minutes |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/onlineStats`
*returns utilization metrics with time series grouped by freqband.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `granularity` | query | string | optional | days/hours/minutes |
| `limit` | query | number($double) | optional | X # of days/hours/minutes |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `500` Internal server error

#### `POST` `/Customers/{id}/locations/{locationId}/qoeMetrics`
*Device or pod QoE 15 minutes data.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `422` if total number of deviceIds and nodeIds == 0 or > 30./div>; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/qoe`
*Device QoE data.*

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `mac` | path | string | **REQUIRED** | mac id of client |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/devices/v2/{mac}/qoe`
*Device QoE with MLO data.*

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `mac` | path | string | **REQUIRED** | mac address of the client |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/{nodeId}/qoe`
*Node QoE data.*

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `nodeId` | path | string | **REQUIRED** | node id |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/v2/{nodeId}/qoe`
*Node QoE data with MLO support.*

**Required to call:** `id` (path), `locationId` (path), `nodeId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `nodeId` | path | string | **REQUIRED** | node id |

**Possible responses:** `200` Request was successful

#### `PATCH` `/Customers/{id}/locations/{locationId}/qoe/liveMode`
*Configure QoE for a location.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/qoe/liveMode`
*Get QoE LiveMode for a location.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/qoe`
*Get QoE recent 1 minute data for a whole location.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/reboots`
*Get reboot count and reason statistic for a whole location.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `nodeId` | query | string | optional |  |
| `startAt` | query | string | optional | find objects after this value, if blank the last 24 hours are returned |
| `endAt` | query | string | optional | find objects before this value |
| `order` | query | string | optional | desc \|\| asc |
| `limit` | query | number($double) | optional | Maximum number of returned entries |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/deviceTypeDetails`
*DeviceType data with ADT*

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `mac` | path | string | **REQUIRED** | mac id of client |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `422` Invalid mac address; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/devices/{mac}/stitchHistory`
*returns Mac stitch history*

**Required to call:** `id` (path), `locationId` (path), `mac` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `mac` | path | string | **REQUIRED** | mac id of client |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `422` Invalid mac address; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/securityPolicy/guard/ohp/problemReports`
*List all problem reports (up tp 7 days) for a given Location ID.*

**Required to call:** `id` (path), `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Success; `401` Authorization required or customer id not found; `404` Location id or WifiNetwork does not exist and is not known to Plume; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/networkOutages/stats`
*aggregate all monthly/yearly network outage stats of the location.*

**Required to call:** `id` (path), `locationId` (path), `startTimestamp` (query), `endTimestamp` (query), `type` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `startTimestamp` | query | number($double) | **REQUIRED** | unix timestamp in milliseconds |
| `endTimestamp` | query | number($double) | **REQUIRED** | unix timestamp in milliseconds |
| `type` | query | string | **REQUIRED** | enum "yearly" or "monthly" |
| `countOnly` | query | boolean | optional | if true, only return the count of events |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location id does not exist; `422` Validation failed; `500` Internal server error

#### `GET` `/Customers/{id}/locations/{locationId}/nodes/health`
*Get node health stats for a location.*

**Required to call:** `id` (path), `locationId` (path), `startDate` (query), `endDate` (query), `granularity` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** | Location ID |
| `startDate` | query | string | **REQUIRED** | Start date in ISO 8601 format (YYYY-MM-DD) |
| `endDate` | query | string | **REQUIRED** | End date in ISO 8601 format (YYYY-MM-DD) |
| `granularity` | query | string | **REQUIRED** | Data granularity: 15m or 3h |
| `timezoneOffset` | query | number($double) | optional | Timezone offset in minutes from UTC (-720 to 840) |

**Possible responses:** `200` Request was successful

#### `GET` `/Customers/{id}/locations/{locationId}/lanConnectivityHistory`
*Get LAN connectivity history for specified MAC addresses.*

**Required to call:** `id` (path), `locationId` (path), `macs` (query), `granularity` (query), `limit` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string($JSON) | **REQUIRED** | Customer id |
| `locationId` | path | string | **REQUIRED** |  |
| `macs` | query | string($JSON) | **REQUIRED** | List of MAC addresses |
| `granularity` | query | string | **REQUIRED** | Data granularity: 15m, 3h, or 1d |
| `limit` | query | number($double) | **REQUIRED** | Number of time periods (e.g., 96 for 24h with 15m granularity) |

**Possible responses:** `200` Success; `401` Authorization required; `404` Location not found; `422` Validation failed

### Gateway
#### `GET` `/gateway/devices/{deviceId}/qoe/history`
*Lighthouse-min device QoE time series (timestamp + weightedQoeScore only).*

**Required to call:** `deviceId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `deviceId` | path | string | **REQUIRED** | Opaque device id encoded as Id().setObjectId(locationId).setMac(mac) |
| `granularity` | query | string | optional | MINUTES/15M/HOURS/3H/DAYS/1D/WEEKS |
| `limit` | query | number($double) | optional | Number of data points to return |

**Possible responses:** `200` Request was successful; `401` Authorization required.; `403` You do not have access to this resource.; `404` Location not found.; `500` An internal error has occurred.

Response example (200):
```json
{
  "items": [
    {
      "timestamp": "2026-05-14T20:45:00.000Z",
      "connection": {
        "weightedQoeScore": 4.62
      }
    }
  ]
}
```

#### `GET` `/gateway/nodes/{serialNumber}/qoe/history`
*Lighthouse-min node QoE time series (timestamp + weightedQoeScore only).*

**Required to call:** `serialNumber` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `serialNumber` | path | string | **REQUIRED** | Node serial number (Node model primary key) |
| `granularity` | query | string | optional | MINUTES/15M/HOURS/3H/DAYS/1D/WEEKS |
| `limit` | query | number($double) | optional | Number of data points to return |

**Possible responses:** `200` Request was successful; `401` Authorization required.; `403` You do not have access to this resource.; `404` Location not found.; `500` An internal error has occurred.

Response example (200):
```json
{
  "items": [
    {
      "timestamp": "2026-05-14T20:45:00.000Z",
      "connection": {
        "weightedQoeScore": 4.62
      }
    }
  ]
}
```

#### `GET` `/gateway/locations/{locationId}/qoe`
*Lighthouse-min location QoE snapshot (per-node + per-device RF + score subset).*

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** | Location id |

**Possible responses:** `200` Request was successful; `401` Authorization required.; `403` You do not have access to this resource.; `404` Location not found.; `500` An internal error has occurred.

Response example (200):
```json
{
  "nodes": [
    {
      "id": "Q0v9n5v48xxx5942333224n64vxb32nmx92970v870",
      "score": 4.78,
      "freqBand": "5G",
      "chWidthMhz": 80,
      "rssiDbm": -42,
      "interferencePercent": 12,
      "snrDb": 38
    }
  ],
  "devices": [
    {
      "mac": "aa:bb:cc:dd:ee:ff",
      "score": 4.21,
      "freqBand": "5G",
      "chWidthMhz": 80,
      "rssiDbm": -52,
      "interferencePercent": 18,
      "snrDb": 32
    }
  ]
}
```

#### `GET` `/gateway/devices/{deviceId}/bandwidth`
*Lighthouse-min daily bandwidth summary for a device (download/upload totals + units).*

**Required to call:** `deviceId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `deviceId` | path | string | **REQUIRED** | Opaque device id encoded as Id().setObjectId(locationId).setMac(mac) |

**Possible responses:** `200` Request was successful; `401` Authorization required.; `403` You do not have access to this resource.; `404` Location not found.; `500` An internal error has occurred.

Response example (200):
```json
{
  "daily": {
    "downloadMb": 4823,
    "uploadMb": 712
  }
}
```

#### `GET` `/gateway/devices/{deviceId}/bandwidth/history`
*Lighthouse-min 24-hour bandwidth time series for a device (15-minute buckets).*

**Required to call:** `deviceId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `deviceId` | path | string | **REQUIRED** | Opaque device id encoded as Id().setObjectId(locationId).setMac(mac) |

**Possible responses:** `200` Request was successful; `401` Authorization required.; `403` You do not have access to this resource.; `404` Location not found.; `500` An internal error has occurred.

Response example (200):
```json
{
  "items": [
    {
      "timestamp": 1714305600000,
      "upload": 12,
      "download": 84
    }
  ]
}
```

#### `GET` `/gateway/locations/{locationId}/devices/bandwidth`
*Per-device daily bandwidth totals (downloadMb/uploadMb) for the requested device ids.*

**Required to call:** `locationId` (path), `deviceIds` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** | Location id |
| `deviceIds` | query | string | **REQUIRED** | JSON array string of opaque device ids (encoded locationId+mac), or a single encoded device id |

**Possible responses:** `200` Request was successful; `401` Authorization required.; `403` You do not have access to this resource.; `404` Location not found.; `422` Validation failed.; `500` An internal error has occurred.

Response example (200):
```json
{
  "items": [
    {
      "mac": "string",
      "downloadMb": 0,
      "uploadMb": 0
    }
  ]
}
```

#### `GET` `/gateway/locations/{locationId}/optimization`
*Location optimization summary (24h aggregate).*

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `200` Request was successful; `401` Authorization required.; `403` You do not have access to this resource.; `404` Location not found.; `422` Validation failed.; `500` An internal error has occurred.

Response example (200):
```json
{
  "eaa": 0,
  "succeeded": 0,
  "failed": 0,
  "total": 0
}
```

#### `GET` `/gateway/locations/{locationId}/reboot/history`
*Location reboot + crash history (items envelope, ISO occurredAt).*

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** | Location id |
| `startAt` | query | string | optional | ISO 8601 start timestamp (default: endAt - 1 day) |
| `endAt` | query | string | optional | ISO 8601 end timestamp (default: now) |
| `order` | query | string | optional | Sort order: asc or desc |
| `limit` | query | number($double) | optional | Max items (1-500, default 100) |

**Possible responses:** `200` Request was successful; `401` Authorization required.; `403` You do not have access to this resource.; `404` Location not found.; `422` Validation failed.; `500` An internal error has occurred.

Response example (200):
```json
{
  "items": [
    {
      "occurredAt": "string",
      "nodeId": "string",
      "reason": "string",
      "firmwareVersion": "string",
      "rebootType": "string",
      "model": "string"
    }
  ]
}
```

#### `GET` `/gateway/devices/{deviceId}/lan-connectivity/history`
*LAN Ethernet connectivity time series for a device (trimmed, ISO timestamps).*

**Required to call:** `deviceId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `deviceId` | path | string | **REQUIRED** | Opaque device id encoded as Id().setObjectId(locationId).setMac(mac) |
| `granularity` | query | string | optional | Data granularity: 15M, 3H, or 1D |
| `limit` | query | number($double) | optional | Number of time periods (e.g., 96 for 24h with 15m granularity) |

**Possible responses:** `200` Request was successful; `401` Authorization required.; `403` You do not have access to this resource.; `404` Location not found.; `422` Validation failed.; `500` An internal error has occurred.

Response example (200):
```json
{
  "statsDateRange": {
    "startAt": "string",
    "endAt": "string"
  },
  "items": [
    {
      "timestamp": "string",
      "isEthernetConnected": true
    }
  ]
}
```

#### `GET` `/gateway/locations/{locationId}/wan-stats/history`
*Lighthouse-min 24h WAN throughput time series (15-minute buckets).*

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** | Location id |

**Possible responses:** `200` Request was successful; `401` Authorization required.; `403` You do not have access to this resource.; `404` Location not found.; `500` An internal error has occurred.

Response example (200):
```json
{
  "items": [
    {
      "timestamp": "2026-05-21T10:15:00.000Z",
      "rxMb": 1234.56,
      "txMb": 78.9,
      "rxMaxMbps": 612.4,
      "txMaxMbps": 41.2
    }
  ]
}
```

#### `GET` `/gateway/locations/{locationId}/wan-saturation`
*Lighthouse-min 24h WAN saturation summary (max rx/tx percentage).*

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** | Location id |

**Possible responses:** `200` Request was successful; `401` Authorization required.; `403` You do not have access to this resource.; `404` Location not found.; `500` An internal error has occurred.

Response example (200):
```json
{
  "rxMaxPercentage": 73.4,
  "txMaxPercentage": 18.1
}
```

#### `GET` `/gateway/locations/{locationId}/wan-saturation/history`
*Lighthouse-min 24h WAN saturation time series (15-minute buckets).*

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** | Location id |

**Possible responses:** `200` Request was successful; `401` Authorization required.; `403` You do not have access to this resource.; `404` Location not found.; `500` An internal error has occurred.

Response example (200):
```json
{
  "items": [
    {
      "timestamp": "2026-05-21T10:15:00.000Z",
      "rxMaxPercentage": 73.4,
      "txMaxPercentage": 12
    }
  ]
}
```

---
## LTE Service API (v1.110.0)
Base URL: `https://piranha-gamma.prod.us-west-2.aws.plumenet.io (LTE server)`

### Locations
#### `POST` `/lteservice/locations/{locationId}/enable`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `201`

#### `POST` `/lteservice/locations/{locationId}/disable`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `201`

#### `POST` `/lteservice/locations/{locationId}/enableOnboarding`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `201`

#### `POST` `/lteservice/locations/{locationId}/disableOnboarding`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `201`

#### `POST` `/lteservice/locations/{locationId}/forceSwitchover`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `202`

#### `GET` `/lteservice/locations/{locationId}/currentState`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `200`

#### `GET` `/lteservice/locations/{locationId}/supported`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `200`

#### `GET` `/lteservice/locations/{locationId}/signalStrength`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `200`

#### `GET` `/lteservice/locations/{locationId}/speedTests`

**Required to call:** `locationId` (path), `limit` (query), `granularity` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** |  |
| `limit` | query | number | **REQUIRED** |  |
| `granularity` | query | string | **REQUIRED** | daysmonths |

**Possible responses:** `200`

#### `GET` `/lteservice/locations/{locationId}/speedTests/{requestId}`

**Required to call:** `locationId` (path), `requestId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** |  |
| `requestId` | path | string | **REQUIRED** |  |

**Possible responses:** `200`

#### `PUT` `/lteservice/locations/{locationId}/speedTest`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `202`

#### `PUT` `/lteservice/locations/{locationId}/configuration`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `202`

#### `GET` `/lteservice/locations/{locationId}/configuration`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `200`

#### `GET` `/lteservice/locations/{locationId}/networkConfiguration`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `200`

Response example (200):
```json
{
  "secondaryNetworks": [
    {
      "networkId": "string",
      "enable": true,
      "wan": true
    }
  ]
}
```

#### `PUT` `/lteservice/locations/{locationId}/networkConfiguration`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `202`

#### `GET` `/lteservice/locations/failures`

**Parameters:** none

**Possible responses:** `200`

Response example (200):
```json
[
  {
    "locationId": "string",
    "partnerId": "string"
  }
]
```

#### `GET` `/lteservice/locations/{locationId}/gdpr`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `200`

#### `GET` `/lteservice/locations/{locationId}/hardwareInfo`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `200`

#### `GET` `/lteservice/locations/{locationId}/ispOutageInfo`

**Required to call:** `locationId` (path), `startDate` (query), `endDate` (query), `type` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** |  |
| `startDate` | query | string | **REQUIRED** | YYYY-MM-DD |
| `endDate` | query | string | **REQUIRED** | YYYY-MM-DD |
| `type` | query | string | **REQUIRED** | monthlyyearly |
| `offsetMinutesfromUTC` | query | number | optional |  |

**Possible responses:** `200`

#### `GET` `/lteservice/locations/{locationId}/dataUsage`

**Required to call:** `locationId` (path), `startDate` (query), `endDate` (query), `type` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** |  |
| `startDate` | query | string | **REQUIRED** | YYYY-MM-DD |
| `endDate` | query | string | **REQUIRED** | YYYY-MM-DD |
| `type` | query | string | **REQUIRED** | monthlyyearly |
| `offsetMinutesfromUTC` | query | number | optional |  |
| `numOfDevices` | query | number | optional |  |

**Possible responses:** `200`

#### `GET` `/lteservice/locations/{locationId}/metrics`

**Required to call:** `locationId` (path), `limitDays` (query)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `locationId` | path | string | **REQUIRED** |  |
| `limitDays` | query | number | **REQUIRED** |  |
| `dataAsArray` | query | boolean | optional | --truefalse |

**Possible responses:** `200`

#### `DELETE` `/lteservice/locations/{id}`

**Required to call:** `id` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `id` | path | string | **REQUIRED** |  |

**Possible responses:** `204`

#### `GET` `/lteservice/locations/{locationId}/liveMetrics`

**Required to call:** `locationId` (path)

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|
| `duration` | query | number | optional |  |
| `superLiveMode` | query | boolean | optional | --truefalse |
| `locationId` | path | string | **REQUIRED** |  |

**Possible responses:** `200`

Response example (200):
```json
[
  {}
]
```

### Health
#### `GET` `/lteservice/health`

**Parameters:** none

**Possible responses:** `200`

Response example (200):
```json
{
  "status": "critical",
  "connections": [
    {
      "resource": "string",
      "description": "string",
      "configurationKeys": [
        [
          "string"
        ]
      ],
      "status": "critical",
      "lastFailure": {
        "timestamp": "string",
        "message": "string"
      },
      "updatedAt": "2026-08-13T20:53:26.763Z"
    }
  ],
  "version": "string",
  "apiVersion": "string"
}
```

### Metrics
#### `GET` `/metrics`

**Parameters:** none

**Possible responses:** `200`

Response example (200):
```json
# HELP healthy Metric that shows if flex is healthy or not.
# TYPE healthy gauge
healthy 1
```

### Version
#### `GET` `/lteservice/version`

**Parameters:** none

**Possible responses:** `200`

Response example (200):
```json
{
  "apiVersion": "string"
}
```
