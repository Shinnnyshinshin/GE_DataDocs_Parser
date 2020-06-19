from great_expectations.core import ExpectationSuiteSchema
from great_expectations.data_context.store.database_store_backend import (
    DatabaseStoreBackend,
)
from great_expectations.data_context.store.store import Store
from great_expectations.data_context.store.tuple_store_backend import TupleStoreBackend
from great_expectations.data_context.types.resource_identifiers import (
    ExpectationSuiteIdentifier,
)
from great_expectations.data_context.util import load_class
from great_expectations.util import verify_dynamic_loading_support


class ExpectationsStore(Store):
    """
An Expectations Store provides a way to store Expectation Suites accessible to a Data Context.

.. admonition:: Feature Maturity

    id: expectations_store_git
    title: Expectation Store - Git
    icon:
    short_description:
    description:
    how_to_guide_url:
    maturity: Production
    maturity_details:
        api_stability: Stable
        implementation_completeness: Complete
        unit_test_coverage: Complete
        integration_infrastructure_test_coverage: N/A
        documentation_completeness: Complete
        bug_risk: Low

    id: expectations_store_filesystem
    title: Expectation Store - Filesystem
    icon:
    short_description:
    description:
    how_to_guide_url:
    maturity: Production
    maturity_details:
        api_stability: Stable
        implementation_completeness: Complete
        unit_test_coverage: Complete
        integration_infrastructure_test_coverage: N/A
        documentation_completeness: Complete
        bug_risk: Low

    id: expectations_store_s3
    title: Expectation Store - S3
    icon:
    short_description:
    description:
    how_to_guide_url:
    maturity: Beta
    maturity_details:
        api_stability: Stable
        implementation_completeness: Complete
        unit_test_coverage: Complete
        integration_infrastructure_test_coverage: Minimal
        documentation_completeness: Complete
        bug_risk: Low

    id: expectations_store_gcs
    title: Expectation Store - GCS
    icon:
    short_description:
    description:
    how_to_guide_url:
    maturity: Beta
    maturity_details:
        api_stability: Stable
        implementation_completeness: Complete
        unit_test_coverage: Complete
        integration_infrastructure_test_coverage: Minimal
        documentation_completeness: Partial
        bug_risk: Low

    id: expectations_store_azure_blob_storage
    title: Expectation Store - Azure
    icon:
    short_description:
    description:
    how_to_guide_url:
    maturity: N/A
    maturity_details:
        api_stability: Stable
        implementation_completeness: Minimal
        unit_test_coverage: Minimal
        integration_infrastructure_test_coverage: Minimal
        documentation_completeness: Minimal
        bug_risk: Moderate
    """

    _key_class = ExpectationSuiteIdentifier

    def __init__(self, store_backend=None, runtime_environment=None):
        self._expectationSuiteSchema = ExpectationSuiteSchema()

        if store_backend is not None:
            store_backend_module_name = store_backend.get(
                "module_name", "great_expectations.data_context.store"
            )
            store_backend_class_name = store_backend.get(
                "class_name", "InMemoryStoreBackend"
            )
            verify_dynamic_loading_support(module_name=store_backend_module_name)
            store_backend_class = load_class(
                store_backend_class_name, store_backend_module_name
            )

            # Store Backend Class was loaded successfully; verify that it is of a correct subclass.
            if issubclass(store_backend_class, TupleStoreBackend):
                # Provide defaults for this common case
                store_backend["filepath_suffix"] = store_backend.get(
                    "filepath_suffix", ".json"
                )
            elif issubclass(store_backend_class, DatabaseStoreBackend):
                # Provide defaults for this common case
                store_backend["table_name"] = store_backend.get(
                    "table_name", "ge_expectations_store"
                )
                store_backend["key_columns"] = store_backend.get(
                    "key_columns", ["expectation_suite_name"]
                )

        super().__init__(
            store_backend=store_backend, runtime_environment=runtime_environment
        )

    def remove_key(self, key):
        return self.store_backend.remove_key(key)

    def serialize(self, key, value):
        return self._expectationSuiteSchema.dumps(value, indent=2, sort_keys=True)

    def deserialize(self, key, value):
        return self._expectationSuiteSchema.loads(value)
