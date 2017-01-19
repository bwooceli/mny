from ofxparse import OfxParser
from .models import *

def ofx_processer(ofxfile, u):
    with ofxfile as fileobj:
        ofx = OfxParser.parse(fileobj)
    
    ofx_results={}
    ofx_results['new_transactions'] = []
    ofx_results['updated_transactions'] = []
    ofx_results['new_accounts'] = []
    ofx_results['updated_accounts'] = []
    
    for ofa in ofx.accounts:
        actype = AccountType.objects.get_or_create(
                account_type = int(ofa.type),
                description = ofa.account_type
                )[0]
        a = Account.objects.get_or_create(
            owner = u,
            number = ofa.number,
            routing_number = ofa.routing_number,
            branch_id = ofa.branch_id,
            account_type = actype,
            curdef = ofa.curdef,
            institution = str(ofa.institution)
        )
        
        #update the statement details if they are newer than what's in the database
        if a[1] or a[0].statement_end_date < ofx.account.statement.end_date:
            a[0].statement_start_date = ofx.account.statement.start_date.replace(hour=0) 
            a[0].statement_end_date = ofx.account.statement.end_date.replace(hour=0)
            a[0].statement_balance = ofx.account.statement.balance 
            a[0].statement_available_balance = ofx.account.statement.available_balance
            a[0].first_balance_date = ofx.account.statement.start_date.replace(hour=0) 

            if a[1]:
                a[0].last_balance = a[0].statement_balance
                a[0].first_balance = a[0].statement_balance
                for transaction in ofx.account.statement.transactions:
                    a[0].first_balance -= transaction.amount

        if a[1]:
            ofx_results['new_accounts'].append(a[0])
        else:
            ofx_results['updated_accounts'].append(a[0])

        a[0].save()

        first_t = Transaction.objects.filter(account=a[0]).order_by('date','order')
        
        if first_t:
            first_t = first_t[0]    
        else:
            first_t = None

        prev_t = None
        next_t = None

        transactions = ofx.account.statement.transactions
        
        transactions.reverse()
        for tr in ofx.account.statement.transactions:
            tr.date = tr.date.replace(hour=0)
            t_obj = Transaction.objects.get_or_create(
                account = a[0],
                date = tr.date,
                number = tr.id
            )
            if t_obj[1]:
                ofx_results['new_transactions'].append(t_obj[0])
            else:
                ofx_results['updated_transactions'].append(t_obj[0])
            
            t = t_obj[0]
            t.transaction_type = tr.type

            t.payee = tr.payee
            t.memo = tr.memo
            if tr.checknum == '':
                tr.checknum = None
            t.checknum = tr.checknum

            t.sic = tr.sic
            t.amount = tr.amount
            
            try:
                mcc = MerchantCategoryCode.objects.get(mcc_id=int(tr.mcc))
                t.mcc = mcc
            except:
                pass
            
            #Set previous and next relationships as well as the OrderedModed order
            
            if first_t:
                if t.date < first_t.date and not prev_t:
                    t.above(first_t)            
                    prev_t = t

            if not prev_t:    
                prev_t = Transaction.objects.filter(date__lt=t.date).order_by('-date', '-order')
                if prev_t:
                    prev_t = prev_t[0]

            if prev_t:
                if not first_t:
                    t.below(prev_t)
                else:
                    first_t = None
            else:
                prev_t = None
            t.save()
            prev_t = t
        if not a[1]:
            a[0].update_current_balance()
    return ofx_results
