import graphene
from graphene_django.types import DjangoObjectType
from graphql_relay.node.node import from_global_id

import json

from . import models

class UserType(DjangoObjectType):
    class Meta:
        model = models.User
        interfaces = (graphene.Node, )

class Query(graphene.AbstractType):
    user = graphene.Field(UserType, id=graphene.ID())

    def resolve_user(self, context, **kwargs):
        rid = from_global_id(args.get('id'))
        # rid is a tuple: ('CompanyType', 1)
        return models.User.objects.get(pk=rid(1))

class CreateUserMutation(graphene.Mutation):
    class Input:
        email = graphene.String()

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
