import graphene
from graphene_django.types import DjangoObjectType
from graphql_relay.node.node import from_global_id

import json

from . import models

class CompanyType(DjangoObjectType):
    class Meta:
        model = models.Company
        interfaces = (graphene.Node, )

class Query(graphene.AbstractType):
    all_companies = graphene.List(CompanyType)

    def resolve_all_companies(self, context, **kwargs):
        return models.Company.objects.all()

    company = graphene.Field(CompanyType, id=graphene.ID())

    def resolve_company(self, context, **kwargs):
        rid = from_global_id(args.get('id'))
        # rid is a tuple: ('CompanyType', 1)
        return models.Company.objects.get(pk=rid(1))

class CreateCompanyMutation(graphene.Mutation):
    class Input:
        company = graphene.String()

    status = graphene.Int()
    formErrors = graphene.String()
    company = graphene.Field(CompanyType)

    @staticmethod
    def mutate(root, args, context, info):
        if not context.user.is_authenticated():
            return CreateMessageMutation(status=403)
        message = args.get('message', '').strip()
        # Here we would usually use Django forms to validate the Input
        if not message:
            return CreateMessageMutation(
                status=400,
                formErrors=json.dumps(
                    {'message': ['Please select a valid company to subscribe to']}
                )
            )
        obj = models
