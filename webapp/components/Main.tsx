import {
  VStack,
} from "@chakra-ui/react"
import useSWR from 'swr'
import axios from 'axios'
import LenderDashboard from "./LenderDashboard"
import BorrowerDashboard from "./BorrowerDashboard"
import AdminDashboard from "./AdminDashboard"
import React from "react";

export const axiosInstance = axios.create({
  baseURL: 'http://localhost:8000/'
});

export enum ShipmentStatus {
    DEFAULTED = "DEFAULTED",
    AWAITING_SHIPMENT = "AWAITING_SHIPMENT",
    SHIPPING = "SHIPPING",
    DELIVERED = "DELIVERED",
}

export enum FinanceStatus{
    NONE = "NONE",
    FINANCED = "FINANCED",
    REPAID = "REPAID",
    DEFAULTED = "DEFAULTED",
}



export interface Invoice {
  id: number
  amount: number
  destination: string
  shippingStatus: ShipmentStatus
  status: FinanceStatus
  // endDate: Date
}



// TODO: Fetch loans from API but use the following for dev
const invoice_fixtures: Invoice[] = [
  {"id":1,"amount":1000,"destination":"Ramesh","status": FinanceStatus.NONE, shippingStatus: ShipmentStatus.AWAITING_SHIPMENT},
  {"id":2,"amount":1000,"destination":"Ajit","status": FinanceStatus.NONE, shippingStatus: ShipmentStatus.AWAITING_SHIPMENT},
  {"id":3,"amount":1000,"destination":"Pavan","status": FinanceStatus.NONE, shippingStatus: ShipmentStatus.AWAITING_SHIPMENT}
]

export const fetcher = url => axiosInstance.get(url).then(res => res.data)

const getInvoices = () => {
  const { data, error } = useSWR<Invoice[]>("invoices", fetcher, { refreshInterval: 1000 })
  console.log('invoices', data)
  return {
    invoices: data,
    isLoading: !error && !data,
    isError: error

    // invoices: invoice_fixtures,
    // isLoading: false,
    // isError: false
  }
}

const Main = () => {
  const { invoices, isLoading, isError } = getInvoices()
  return (
  <VStack align="left" textAlign="left" p="20px">
    <LenderDashboard invoices={invoices} isLoading={isLoading} isError={isError} />
    <AdminDashboard invoices={invoices} isLoading={isLoading} isError={isError} />
    <BorrowerDashboard/>
  </VStack>
  )
}

export default Main
