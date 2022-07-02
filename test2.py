import urllib


str1= b'data=%0A++++++++%3C%3Fxml+version%3D%221.0%22+encoding%3D%22UTF-8%22+%3F%3E%3Centry+xmlns%3D%22http%3A%2F%2Fpurl.org%2Fatom%2Fns%23%22%3E%09%3CJob.getList%3E%09%09%3CqueryCondition%3EfullPath+%3D+%27%5C10+As+Of+ledger+posting+%5C%28R41542++PSAG0008%5C%29%27%3C%2FqueryCondition%3E%09%09%3CselectColumns%2F%3E%09%09%3CnumRows%3E1%3C%2FnumRows%3E%09%3C%2FJob.getList%3E%3C%2Fentry%3E%0A++++++++'
print(str1.decode('utf-8'))
print( urllib.parse.unquote_plus(str1.decode('utf-8')))