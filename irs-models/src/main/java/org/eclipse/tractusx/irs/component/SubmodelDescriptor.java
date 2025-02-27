/********************************************************************************
 * Copyright (c) 2021,2022,2023
 *       2022: ZF Friedrichshafen AG
 *       2022: ISTOS GmbH
 *       2022,2023: Bayerische Motoren Werke Aktiengesellschaft (BMW AG)
 *       2022,2023: BOSCH AG
 * Copyright (c) 2021,2022,2023 Contributors to the Eclipse Foundation
 *
 * See the NOTICE file(s) distributed with this work for additional
 * information regarding copyright ownership.
 *
 * This program and the accompanying materials are made available under the
 * terms of the Apache License, Version 2.0 which is available at
 * https://www.apache.org/licenses/LICENSE-2.0.
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 *
 * SPDX-License-Identifier: Apache-2.0
 ********************************************************************************/
package org.eclipse.tractusx.irs.component;

import java.util.List;

import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import com.fasterxml.jackson.databind.annotation.JsonPOJOBuilder;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Singular;
import lombok.Value;

/**
 * SubmodelDescriptor description
 */
@Value
@Builder(toBuilder = true)
@AllArgsConstructor
@JsonDeserialize(builder = SubmodelDescriptor.SubmodelDescriptorBuilder.class)
public class SubmodelDescriptor {

    @Schema(implementation = String.class)
    private String identification;

    @Schema(implementation = String.class)
    private String idShort;

    @Schema()
    @Singular
    private List<Description> descriptions;

    @Schema(implementation = SemanticId.class)
    private SemanticId semanticId;

    @Schema()
    @Singular
    private List<Endpoint> endpoints;

    /**
     * User to build SubmodelDescriptor
     */
    @Schema(description = "User to build async fetched items")
    @JsonPOJOBuilder(withPrefix = "")
    public static class SubmodelDescriptorBuilder {
    }
}
