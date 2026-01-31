"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import type { City } from "@/types";
import { useCreateCity, useUpdateCity } from "@/hooks/use-cities";

const citySchema = z.object({
  name: z.string().min(1, "请输入城市名称"),
  province: z.string().min(1, "请输入省份"),
  tier: z.enum(["tier1", "new_tier1", "tier2", "tier3"]),
  enabled: z.boolean(),
});

type CityFormData = z.infer<typeof citySchema>;

interface CityFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  city?: City | null;
}

const tierOptions = [
  { value: "tier1", label: "一线城市" },
  { value: "new_tier1", label: "新一线城市" },
  { value: "tier2", label: "二线城市" },
  { value: "tier3", label: "三线城市" },
];

export function CityFormDialog({
  open,
  onOpenChange,
  city,
}: CityFormDialogProps) {
  const createCity = useCreateCity();
  const updateCity = useUpdateCity();
  const isEditing = !!city;

  const form = useForm<CityFormData>({
    resolver: zodResolver(citySchema),
    defaultValues: {
      name: "",
      province: "",
      tier: "tier2",
      enabled: true,
    },
  });

  useEffect(() => {
    if (city) {
      form.reset({
        name: city.name,
        province: city.province,
        tier: city.tier,
        enabled: city.enabled,
      });
    } else {
      form.reset({
        name: "",
        province: "",
        tier: "tier2",
        enabled: true,
      });
    }
  }, [city, form]);

  const onSubmit = async (data: CityFormData) => {
    try {
      if (isEditing && city) {
        await updateCity.mutateAsync({ id: city.id, data });
      } else {
        await createCity.mutateAsync(data);
      }
      onOpenChange(false);
    } catch {
      // Error handled by mutation
    }
  };

  const isLoading = createCity.isPending || updateCity.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{isEditing ? "编辑城市" : "添加城市"}</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>城市名称</FormLabel>
                  <FormControl>
                    <Input placeholder="例如：深圳" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="province"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>省份</FormLabel>
                  <FormControl>
                    <Input placeholder="例如：广东" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="tier"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>城市级别</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                    value={field.value}
                  >
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="选择城市级别" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      {tierOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="enabled"
              render={({ field }) => (
                <FormItem className="flex items-center justify-between rounded-lg border p-3">
                  <div className="space-y-0.5">
                    <FormLabel>启用状态</FormLabel>
                    <p className="text-sm text-muted-foreground">
                      启用后将参与数据采集
                    </p>
                  </div>
                  <FormControl>
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                </FormItem>
              )}
            />

            <div className="flex justify-end gap-2 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                取消
              </Button>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? "保存中..." : isEditing ? "更新" : "添加"}
              </Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
